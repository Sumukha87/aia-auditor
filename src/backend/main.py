from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import ollama
from qdrant_client import QdrantClient
import os

app = FastAPI(title="AIA Backend Core")

# Connect to Qdrant (Internal Docker Network)
client = QdrantClient(host="qdrant", port=6333)
COLLECTION = "cloud_knowledge_vault"

class AuditRequest(BaseModel):
    text: str
    mode: str
    internal_key: str

@app.post("/api/v1/audit")
async def process_audit(req: AuditRequest):
    # Security: Verify the request is from our frontend
    if req.internal_key != os.getenv("INTERNAL_API_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

    # 1. RAG: Search context from memory
    vector = ollama.embeddings(model="nomic-embed-text", prompt=req.text)["embedding"]
    
    # Apply category filter if auditing
    q_filter = {"must": [{"key": "category", "match": {"value": "benchmarks"}}]} if req.mode == "audit" else None

    results = client.search(collection_name=COLLECTION, query_vector=vector, query_filter=q_filter, limit=5)
    context = "\n".join([f"SOURCE: {h.payload['source']}\n{h.payload['text']}" for h in results])

    # 2. LLM: Generate the report
    prompt = f"SYSTEM: You are a Senior Security Architect. Context:\n{context}\n\nUSER: {req.text}"
    response = ollama.chat(model="qwen2.5-coder:7b", messages=[{'role': 'user', 'content': prompt}])
    
    return {"report": response['message']['content'], "sources": [h.payload['source'] for h in results]}