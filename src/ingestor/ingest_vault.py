import os
import uuid
import ollama
import pandas as pd
from pathlib import Path
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from langchain_text_splitters import RecursiveCharacterTextSplitter

client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "cloud_knowledge_vault"

if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)

def ingest_file(file_path, category):
    text = ""
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        reader = PdfReader(file_path)
        text = "".join([page.extract_text() for page in reader.pages])
    elif ext in [".txt", ".md"]:
        text = file_path.read_text()
    elif ext == ".xlsx":
        # For Excel, we turn each row into a text string
        df = pd.read_excel(file_path)
        text = df.to_string() 
    
    if not text.strip(): return

    chunks = splitter.split_text(text)
    points = []
    for chunk in chunks:
        # Generate embedding on your 4060
        vector = ollama.embeddings(model="nomic-embed-text", prompt=chunk)["embedding"]
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text": chunk, 
                "category": category, 
                "source": file_path.name
            }
        ))
    client.upsert(collection_name=COLLECTION_NAME, points=points)

def build_vault():
    base_path = Path("data/knowledge")
    for category_dir in base_path.iterdir():
        if not category_dir.is_dir(): continue
        for file_path in category_dir.glob("*.*"):
            print(f"🧬 Ingesting {file_path.name}...")
            ingest_file(file_path, category_dir.name)

if __name__ == "__main__":
    build_vault()
    print("✅ Vault is fully loaded with PDFs, Excel mappings, and Custom Rules.")