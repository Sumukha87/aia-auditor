import ollama
from qdrant_client import QdrantClient

# 1. Connect to the Memory
client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "infra_rules"

def search_rules(user_query):
    # 1. Turn the question into numbers
    response = ollama.embeddings(model="nomic-embed-text", prompt=user_query)
    query_vector = response["embedding"]

    # 2. Use the modern query_points method
    search_results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,  # In the new API, 'query_vector' became just 'query'
        limit=2
    ).points

    print(f"\n🔍 Searching for: '{user_query}'")
    for hit in search_results:
        # Note: In query_points, the results are in a .points list
        print(f"✅ Found Rule (Score: {hit.score:.3f}): {hit.payload['text'].strip()}")

# Test the search
search_rules("Is it okay to have open ssh ports?")
search_rules("How should I handle user login?")