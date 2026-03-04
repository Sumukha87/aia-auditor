import streamlit as st
import requests
import hmac
import os
import datetime # Added for filename dating
from pypdf import PdfReader
from fpdf import FPDF # Added for PDF generation
from dotenv import load_dotenv

# --- 1. CORE CONFIGURATION ---
load_dotenv()
API_URL = "http://backend:8000"
INTERNAL_KEY = os.getenv("INTERNAL_API_KEY", "system_secret_123")
MASTER_PASSWORD = os.getenv("APP_PASSWORD")

st.set_page_config(
    page_title="AIA | Advanced Infra Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- NEW: PDF GENERATOR HELPER ---
def create_pdf(report_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "AIA AUDITOR - SECURITY REPORT", align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", align='R', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font("helvetica", "", 12)
    # Clean text to prevent encoding errors
    clean_text = report_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    
    return bytes(pdf.output())

def check_password():
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("<h2 style='text-align:center; color:#00ffcc;'>🛡️ AIA AUDITOR ACCESS</h2>", unsafe_allow_html=True)
    master_pwd = os.environ.get("APP_PASSWORD")

    with st.form("login_form"):
        pwd_input = st.text_input("ENTER SYSTEM ACCESS KEY", type="password")
        submit_button = st.form_submit_button("AUTHENTICATE")

        if submit_button:
            if master_pwd and hmac.compare_digest(pwd_input, master_pwd):
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ ACCESS DENIED")
    return False

# --- 3. CUSTOM CYBER-SECURITY CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    .stApp { background: radial-gradient(circle at top right, #0a0e17, #000000); color: #e0e0e0; font-family: 'JetBrains Mono', monospace; }
    [data-testid="stSidebar"] { background-color: rgba(20, 20, 20, 0.9) !important; border-right: 2px solid #00ffcc33; }
    .audit-card { background: rgba(15, 25, 35, 0.8); border: 1px solid #00ffcc55; padding: 25px; border-radius: 15px; box-shadow: 0 0 20px rgba(0, 255, 204, 0.1); color: #f0f0f0; line-height: 1.6; }
    .stButton>button { background: transparent !important; color: #00ffcc !important; border: 2px solid #00ffcc !important; width: 100%; font-weight: bold; letter-spacing: 2px; transition: 0.3s; }
    .stButton>button:hover { background: #00ffcc !important; color: #000 !important; box-shadow: 0 0 25px #00ffcc; }
    .status-pulse { height: 10px; width: 10px; background-color: #00ffcc; border-radius: 50%; display: inline-block; animation: pulse 1.5s infinite; margin-right: 10px; }
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(0, 255, 204, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(0, 255, 204, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 255, 204, 0); } }
    </style>
    """, unsafe_allow_html=True)

# --- 4. MAIN INTERFACE ---
if check_password():
    with st.sidebar:
        st.markdown("<h1 style='color: #00ffcc;'>SYSTEM CORE</h1>", unsafe_allow_html=True)
        mode = st.radio("OPERATION MODE", ["Audit Code", "General Question", "Review Uploads"])
        
        st.divider()
        st.subheader("📤 INGEST INTEL")
        uploaded_file = st.file_uploader("Upload Cloud Docs", type=["pdf", "txt"], label_visibility="collapsed")
        
        if uploaded_file and st.button("🚀 EXECUTE INGESTION"):
            with st.spinner("Slicing and Embedding..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                headers = {"X-Internal-Key": INTERNAL_KEY}
                resp = requests.post(f"{API_URL}/api/v1/ingest", files=files, headers=headers)
                if resp.status_code == 200:
                    st.success(f"Merged {uploaded_file.name} into Vault.")
                else:
                    st.error("Ingestion failed.")

        st.divider()
        if st.button("TERMINATE SESSION"):
            st.session_state["password_correct"] = False
            st.rerun()

    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"# <span style='color:#00ffcc;'>{mode.upper()}</span>", unsafe_allow_html=True)
    with c2:
        st.markdown("<br><div class='status-pulse'></div><b>SYSTEMS READY</b>", unsafe_allow_html=True)

    if mode == "Audit Code":
        user_input = st.text_area("PASTE TERRAFORM / CLOUD CODE:", height=300)
    elif mode == "Review Uploads":
        user_input = st.text_input("QUERY UPLOADED DOCUMENTS:")
    else:
        user_input = st.text_input("ASK A GENERAL CLOUD SECURITY QUESTION:")

    if st.button("INITIATE ANALYSIS"):
        if not user_input.strip():
            st.warning("Input buffer empty.")
        else:
            with st.status("🔍 Scanning Vault...", expanded=True) as status:
                payload = {"text": user_input, "mode": mode.lower().replace(" ", "_"), "internal_key": INTERNAL_KEY}
                try:
                    response = requests.post(f"{API_URL}/api/v1/audit", json=payload, timeout=90)
                    if response.status_code == 200:
                        data = response.json()
                        status.update(label="Analysis Completed.", state="complete", expanded=False)
                        
                        st.markdown("### 🤖 ASSISTANT REPORT")
                        st.markdown(f"<div class='audit-card'>{data['report']}</div>", unsafe_allow_html=True)
                        
                        # --- THE ADDITION: DOWNLOAD BUTTON ---
                        st.divider()
                        pdf_bytes = create_pdf(data['report'])
                        st.download_button(
                            label="📥 DOWNLOAD AUDIT REPORT (PDF)",
                            data=pdf_bytes,
                            file_name=f"AIA_Audit_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            mime="application/pdf"
                        )

                        with st.expander("📚 VIEW DATA SOURCES"):
                            for src in data.get('sources', []):
                                st.write(f"• {src}")
                    else:
                        st.error(f"Core Error: {response.status_code}")
                except Exception as e:
                    st.error(f"📡 Backend Connection Failed: {e}")

st.markdown("<br><hr><center style='color: #444;'>AIA-AUDITOR v2.5 | POWERED BY RTX 4060</center>", unsafe_allow_html=True)