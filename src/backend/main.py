from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from pypdf import PdfReader
import os
import uvicorn
import time
import subprocess
import uuid
import io

app = FastAPI(title="AIA Backend Core")

# --- AUTO-PULL MODELS ON STARTUP ---
@app.on_event("startup")
async def startup_event():
    """Ensures Ollama models are available before the first request hits."""
    required_models = ["nomic-embed-text", "qwen2.5:0.5b"]
    
    # Wait for the 'ollama serve' background process to wake up
    time.sleep(5) 
    
    for model in required_models:
        try:
            print(f"Checking for model: {model}...")
            # We use subprocess to pull directly via the CLI
            subprocess.run(["ollama", "pull", model], check=True)
            print(f"✅ Model {model} is ready.")
        except Exception as e:
            print(f"⚠️ Error pulling {model}: {e}")

# --- CONFIGURATION ---
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
INTERNAL_KEY = os.getenv("INTERNAL_API_KEY")
COLLECTION = "cloud_knowledge_vault"

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

# --- MISSING ENDPOINT ADDED HERE: INGEST ---
@app.post("/api/v1/ingest")
async def process_ingest(
    file: UploadFile = File(...),
    category: str = Form("benchmarks"), 
    internal_key: str = Form(...)
):
    # Security check
    if internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        print(f"📥 Receiving file: {file.filename}")
        
        # 1. Read the file
        file_bytes = await file.read()
        text = ""
        
        # 2. Extract Text based on file type
        if file.filename.lower().endswith(".pdf"):
            pdf = PdfReader(io.BytesIO(file_bytes))
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
            
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file.")

        # 3. Chunk the text (1000 characters per chunk)
        chunk_size = 1000
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        # 4. Create Embeddings
        points = []
        for chunk in chunks:
            if not chunk.strip(): continue
            
            vector_res = ollama.embeddings(model="nomic-embed-text", prompt=chunk)
            
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector_res["embedding"],
                payload={
                    "text": chunk, 
                    "source": file.filename, 
                    "category": category
                }
            ))

        # 5. Upload to Qdrant Database
        client.upsert(
            collection_name=COLLECTION,
            points=points
        )
        
        print(f"✅ Successfully ingested {len(points)} chunks into Qdrant.")
        return {"status": "success", "chunks_processed": len(points), "filename": file.filename}

    except Exception as e:
        print(f"❌ INGEST ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest file: {str(e)}")

# --- EXISTING ENDPOINT: AUDIT ---
@app.post("/api/v1/audit")
async def process_audit(req: AuditRequest):
    if req.internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        # 1. RAG: Search context
        vector_res = ollama.embeddings(model="nomic-embed-text", prompt=req.text)
        vector = vector_res["embedding"]
        
        q_filter = {"must": [{"key": "category", "match": {"value": "benchmarks"}}]} if req.mode == "audit" else None

        results = client.query_points(
            collection_name=COLLECTION, 
            query=vector, 
            query_filter=q_filter, 
            limit=5
        ).points
        
        context = "\n".join([f"SOURCE: {h.payload.get('source', 'Unknown')}\n{h.payload.get('text', '')}" for h in results])

        # 2. LLM: Generate the report
        prompt = f"SYSTEM: You are a Senior Security Architect. Context:\n{context}\n\nUSER: {req.text}"
        response = ollama.chat(model="qwen2.5:0.5b", messages=[{'role': 'user', 'content': prompt}])
        
        return {
            "report": response['message']['content'], 
            "sources": [h.payload.get('source') for h in results if h.payload]
        }
    except Exception as e:
        print(f"❌ AI PROCESSING ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)