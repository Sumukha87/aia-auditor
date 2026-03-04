import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# --- Configuration ---
client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "cloud_knowledge_vault" # Updated name
MODEL_AUDITOR = "qwen2.5-coder:7b"
MODEL_EMBED = "nomic-embed-text"

def get_context(user_input, mode="general"):
    """
    Retrieves chunks with optional category filtering.
    Modes: 'audit' (benchmarks only), 'general' (everything)
    """
    resp = ollama.embeddings(model=MODEL_EMBED, prompt=user_input)
    
    # Define metadata filter based on mode
    query_filter = None
    if mode == "audit":
        query_filter = Filter(
            must=[FieldCondition(key="category", match=MatchValue(value="benchmarks"))]
        )

    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=resp["embedding"],
        query_filter=query_filter,
        limit=7  # Increased limit because you have much more data now
    )
    
    context_text = ""
    for hit in search_results:
        source = hit.payload.get("source", "Unknown")
        category = hit.payload.get("category", "General")
        content = hit.payload.get("text", "")
        context_text += f"\n---\nSOURCE: [{category}] {source}\nCONTENT: {content}\n"
    return context_text

def run_assistant(user_input):
    # Detection: Is it code or a question?
    is_code = "resource" in user_input or "module" in user_input or "{" in user_input
    mode = "audit" if is_code else "general"
    
    context = get_context(user_input, mode=mode)
    
    system_prompt = f"""
    You are a Senior Multi-Cloud Security Architect and Compliance Expert.
    You have access to CIS Benchmarks, NIST 800-53 mappings, and Official Cloud Docs.

    CONTEXT FROM KNOWLEDGE VAULT:
    {context}

    INSTRUCTIONS:
    1. If auditing CODE: Identify violations against CIS/NIST standards found in context. 
       Provide Severity, Rule ID, and a 'Remediation' code block.
    2. If answering a QUESTION: Use the Official Docs and Benchmarks to provide a detailed technical answer.
    3. ALWAYS cite the 'SOURCE' name provided in the context.
    4. If the context doesn't have the answer, use your internal knowledge but clearly state: "Based on general best practices (not found in vault)..."
    """

    print(f"🔍 Mode: {mode.upper()} | 🧠 Thinking...")
    response = ollama.chat(model=MODEL_AUDITOR, messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_input}
    ])
    
    return response['message']['content']

# --- INTERACTIVE LOOP ---
print("--- 🛡️  UNIVERSAL CLOUD SECURITY ASSISTANT IS ONLINE ---")
print("I can audit Terraform, explain NIST controls, or answer cloud questions.")
print("Type 'exit' to stop.\n")

while True:
    user_msg = input("\n👤 YOU: ")
    
    if user_msg.lower() in ['exit', 'quit']:
        break
        
    if not user_msg.strip():
        continue

    report = run_assistant(user_msg)
    print("\n--- 🤖 ASSISTANT REPORT ---")
    print(report)
    print("\n" + "="*50)