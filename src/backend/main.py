from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama
from qdrant_client import QdrantClient
import os
import uvicorn

app = FastAPI(title="AIA Backend Core")

# --- GCP CONFIGURATION ---
# These will be set in your Terraform / Cloud Run Env Variables
QDRANT_URL = os.getenv("QDRANT_URL") # e.g., "https://xyz-example.gcp.cloud.qdrant.io"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
INTERNAL_KEY = os.getenv("INTERNAL_API_KEY")
COLLECTION = "cloud_knowledge_vault"

# Initialize Client
# This works for both Qdrant Cloud (https) and local testing
client = QdrantClient(
    url=QDRANT_URL, 
    api_key=QDRANT_API_KEY,
    timeout=60
)

class AuditRequest(BaseModel):
    text: str
    mode: str
    internal_key: str

@app.get("/health")
async def health():
    return {"status": "alive"}

@app.post("/api/v1/audit")
async def process_audit(req: AuditRequest):
    # Security check
    if req.internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        # 1. RAG: Search context
        # Note: Ensure "nomic-embed-text" is pulled in your start.sh
        vector_res = ollama.embeddings(model="nomic-embed-text", prompt=req.text)
        vector = vector_res["embedding"]
        
        # Apply filter
        q_filter = {"must": [{"key": "category", "match": {"value": "benchmarks"}}]} if req.mode == "audit" else None

        results = client.query_points(
            collection_name=COLLECTION, 
            query=vector, 
            query_filter=q_filter, 
            limit=5
        ).points
        
        context = "\n".join([f"SOURCE: {h.payload.get('source', 'Unknown')}\n{h.payload.get('text', '')}" for h in results])

        # 2. LLM: Generate the report
        # We use qwen2.5:0.5b to fit in the 2GB RAM limit of standard Cloud Run
        prompt = f"SYSTEM: You are a Senior Security Architect. Context:\n{context}\n\nUSER: {req.text}"
        response = ollama.chat(model="qwen2.5:0.5b", messages=[{'role': 'user', 'content': prompt}])
        
        return {
            "report": response['message']['content'], 
            "sources": [h.payload.get('source') for h in results if h.payload]
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error during AI processing")

if __name__ == "__main__":
    # Cloud Run requires the app to listen on the $PORT environment variable (usually 8080)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)