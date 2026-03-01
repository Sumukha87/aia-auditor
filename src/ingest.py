import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 1. Connect to Qdrant (Memory)
client = QdrantClient(host="localhost", port=6333)

# 2. Create a "Collection" (like a database table)
COLLECTION_NAME = "infra_rules"
if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE), # 768 is the size for nomic-embed-text
    )

# 3. Read our Knowledge file
with open("data/knowledge/gcp_security.txt", "r") as f:
    rules = f.readlines()

print(f"📥 Processing {len(rules)} rules...")

# 4. Embed and Store
for i, rule in enumerate(rules):
    if not rule.strip(): continue
    
    # Use Ollama to turn text into a list of numbers (Vector)
    # This runs on your 4060!
    response = ollama.embeddings(model="nomic-embed-text", prompt=rule)
    embedding = response["embedding"]

    # Save to Qdrant
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(id=i, vector=embedding, payload={"text": rule})
        ]
    )

print("✅ Knowledge stored in local memory.")