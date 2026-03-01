import uuid
import ollama
import fitz  # PyMuPDF
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "cloud_security_benchmarks"

# 2. Define the Text Splitter (The missing piece!)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=200
)

# 3. Create the collection if it doesn't exist
if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )

def ingest_pdf(pdf_path, provider):
    print(f"📂 Opening {pdf_path}...")
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    # Use the splitter defined above
    chunks = text_splitter.split_text(full_text)
    print(f"📄 Found {len(chunks)} chunks in {pdf_path}")

    for i, chunk in enumerate(chunks):
        # Generate Vector on your 4060
        resp = ollama.embeddings(model="nomic-embed-text", prompt=chunk)
        
        # UUID fix for Qdrant compatibility
        point_id = str(uuid.uuid4())

        # Store in Qdrant
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=point_id, 
                vector=resp["embedding"], 
                payload={
                    "text": chunk, 
                    "provider": provider, 
                    "source": pdf_path,
                    "chunk_index": i
                }
            )]
        )
        if i % 50 == 0:
            print(f"  ... Indexed {i} chunks")

    print(f"✅ Finished indexing {pdf_path}")

# Run the ingestion
if __name__ == "__main__":
    pdf_file = "data/knowledge/azure/CIS_Microsoft_Azure_Foundations_Benchmark_v5.0.0.pdf"
    ingest_pdf(pdf_file, "azure")