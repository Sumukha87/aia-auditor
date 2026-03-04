import streamlit as st
import requests
import hmac
import os
import uuid
from pypdf import PdfReader

# --- 1. CORE CONFIGURATION ---
# Points to your FastAPI container in the Docker network
API_URL = os.getenv("API_URL", "http://backend:8000")
INTERNAL_KEY = os.getenv("INTERNAL_API_KEY", "system_secret_123")

st.set_page_config(
    page_title="AIA | Advanced Infra Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. THE SECURITY GATEKEEPER ---
def check_password():
    """Returns True if the user provides the correct access key."""
    if st.session_state.get("password_correct", False):
        return True

    def password_entered():
        # Use hmac for secure comparison
        if hmac.compare_digest(st.session_state["password"], "admin123"): 
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    st.markdown("""
        <div style='text-align: center; padding: 100px 0px;'>
            <h1 style='color: #00ffcc; font-family: "JetBrains Mono", monospace;'>🛡️ Super Duper Ai Cloud Assistant </h1>
            <p style='color: #888;'>ENCRYPTED TERMINAL ACCESS REQUIRED</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.text_input("ENTER SYSTEM ACCESS KEY", type="password", on_change=password_entered, key="password")
    
    if st.session_state.get("password_correct") == False:
        st.error("❌ ACCESS DENIED: INVALID CREDENTIALS")
    return False

# --- 3. CUSTOM CYBER-SECURITY CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    
    .stApp {
        background: radial-gradient(circle at top right, #0a0e17, #000000);
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
    }

    [data-testid="stSidebar"] {
        background-color: rgba(20, 20, 20, 0.9) !important;
        border-right: 2px solid #00ffcc33;
    }

    .audit-card {
        background: rgba(15, 25, 35, 0.8);
        border: 1px solid #00ffcc55;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.1);
        color: #f0f0f0;
        line-height: 1.6;
    }

    .stButton>button {
        background: transparent !important;
        color: #00ffcc !important;
        border: 2px solid #00ffcc !important;
        width: 100%;
        font-weight: bold;
        letter-spacing: 2px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background: #00ffcc !important;
        color: #000 !important;
        box-shadow: 0 0 25px #00ffcc;
    }

    .status-pulse {
        height: 10px; width: 10px;
        background-color: #00ffcc;
        border-radius: 50%;
        display: inline-block;
        animation: pulse 1.5s infinite;
        margin-right: 10px;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 255, 204, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(0, 255, 204, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 255, 204, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. MAIN INTERFACE ---
if check_password():
    # Sidebar: Knowledge & Mode Management
    with st.sidebar:
        st.markdown("<h1 style='color: #00ffcc;'>SYSTEM CORE</h1>", unsafe_allow_html=True)
        mode = st.radio("OPERATION MODE", ["Audit Code", "General Question", "Review Uploads"])
        
        st.divider()
        st.subheader("📤 INGEST INTEL")
        uploaded_file = st.file_uploader("Upload Cloud Docs (PDF/TXT)", type=["pdf", "txt"], label_visibility="collapsed")
        
        if uploaded_file and st.button("🚀 EXECUTE INGESTION"):
            with st.spinner("Slicing and Embedding..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                headers = {"X-Internal-Key": INTERNAL_KEY}
                # This calls your Backend's ingestion endpoint
                resp = requests.post(f"{API_URL}/api/v1/ingest", files=files, headers=headers)
                if resp.status_code == 200:
                    st.success(f"Merged {uploaded_file.name} into Vault.")
                else:
                    st.error("Ingestion failed at Core.")

        st.divider()
        if st.button("TERMINATE SESSION"):
            st.session_state["password_correct"] = False
            st.rerun()

    # Main Dashboard Header
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"# <span style='color:#00ffcc;'>{mode.upper()}</span>", unsafe_allow_html=True)
    with c2:
        st.markdown("<br><div class='status-pulse'></div><b>SYSTEMS READY</b>", unsafe_allow_html=True)

    # Input Areas
    if mode == "Audit Code":
        user_input = st.text_area("PASTE TERRAFORM / CLOUD CODE:", height=300, placeholder="resource 'google_compute_instance' ...")
    elif mode == "Review Uploads":
        user_input = st.text_input("QUERY UPLOADED DOCUMENTS:", placeholder="What are the specific requirements in the design doc?")
    else:
        user_input = st.text_input("ASK A GENERAL CLOUD SECURITY QUESTION:", placeholder="How do I secure a GCP Project?")

    # Action Trigger
    if st.button("INITIATE ANALYSIS"):
        if not user_input.strip():
            st.warning("Input buffer empty.")
        else:
            with st.status("🔍 Scanning Vault and Processing with Qwen...", expanded=True) as status:
                payload = {
                    "text": user_input,
                    "mode": mode.lower().replace(" ", "_"),
                    "internal_key": INTERNAL_KEY
                }
                
                try:
                    # Communicate with the Backend Service
                    response = requests.post(f"{API_URL}/api/v1/audit", json=payload, timeout=90)
                    
                    if response.status_code == 200:
                        data = response.json()
                        status.update(label="Analysis Completed.", state="complete", expanded=False)
                        
                        st.markdown("### 🤖 ASSISTANT REPORT")
                        st.markdown(f"<div class='audit-card'>{data['report']}</div>", unsafe_allow_html=True)
                        
                        with st.expander("📚 VIEW DATA SOURCES"):
                            for src in data.get('sources', []):
                                st.write(f"• {src}")
                    else:
                        st.error(f"Core Error: {response.status_code}")
                except Exception as e:
                    st.error(f"📡 Backend Connection Failed: {e}")

# --- Footer ---
st.markdown("<br><hr><center style='color: #444;'>AIA-AUDITOR v2.5 | POWERED BY RTX 4060</center>", unsafe_allow_html=True)