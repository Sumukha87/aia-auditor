import ollama
import uuid
from qdrant_client import QdrantClient

# --- Configuration ---
client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "cloud_security_benchmarks"
MODEL_AUDITOR = "qwen2.5-coder:7b"
MODEL_EMBED = "nomic-embed-text"

def get_context(user_input):
    """Retrieves the most relevant 5 chunks from our PDF-based memory."""
    resp = ollama.embeddings(model=MODEL_EMBED, prompt=user_input)
    search_results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=resp["embedding"],
        limit=5  # Increased to 5 for better PDF coverage
    ).points
    
    context_text = ""
    for hit in search_results:
        source = hit.payload.get("source", "Unknown")
        content = hit.payload.get("text", "")
        context_text += f"\n---\nSOURCE: {source}\nRULE/CONTENT: {content}\n"
    return context_text

def run_audit(user_input):
    context = get_context(user_input)
    
    system_prompt = f"""
    You are a Professional Cloud Security Architect. 
    Your task is to analyze the user's input based ONLY on the provided SECURITY RULES.

    SECURITY RULES FROM MEMORY:
    {context}

    INSTRUCTIONS:
    1. If the input is Terraform/Cloud code: Identify violations, give severity (High/Med/Low), and provide a 'Remediation' code block.
    2. If the input is a question: Answer it accurately using the rules and cite the SOURCE.
    3. If the rules don't contain the answer, say 'I don't have enough information in my current security benchmarks.'
    """

    print("\n🧠 Thinking...")
    response = ollama.chat(model=MODEL_AUDITOR, messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_input}
    ])
    
    return response['message']['content']

# --- INTERACTIVE LOOP ---
print("--- 🛡️  LOCAL CLOUD SECURITY AUDITOR IS ONLINE ---")
print("Type your security question or paste Terraform code below.")
print("Type 'exit' or 'quit' to stop.\n")

while True:
    user_msg = input("\n👤 YOU: ")
    
    if user_msg.lower() in ['exit', 'quit']:
        print("Stopping Auditor. Stay secure!")
        break
        
    if not user_msg.strip():
        continue

    report = run_audit(user_msg)
    print("\n--- 🤖 AUDITOR REPORT ---")
    print(report)
    print("\n" + "="*50)