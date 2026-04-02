import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Guild Rally Attendance Portal",
    page_icon="⚔️",
    layout="wide"
)

# Gaming-style UI enhancements
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #2ecc71;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #27ae60;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION & PRIVACY ---
def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.title("🛡️ Guild Access Control")
        pwd = st.text_input("Enter Guild Member Password", type="password")
        if st.button("Unlock Portal"):
            if pwd == st.secrets.get("APP_PASSWORD", "admin123"): # Default if not set
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("🚫 Incorrect Password")
        return False
    return True

if not check_password():
    st.stop()

# --- 3. API SETUP ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
    else:
        API_KEY = st.sidebar.text_input("Manual API Key (Development Only)", type="password")
    
    if API_KEY:
        genai.configure(api_key=API_KEY)
        # Using Gemini 3 Flash for peak 2026 performance
        model = genai.GenerativeModel('gemini-3-flash-preview')
    else:
        st.warning("⚠️ API Key missing. Please check Streamlit Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Config Error: {e}")
    st.stop()

# --- 4. UI HEADER ---
st.title("⚔️ Guild Rally Attendance Portal")
st.write("Automatically extract rally participants while ignoring leaders and marking absences.")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_files = st.file_uploader(
        "Drop Rally Screenshots Here", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )

with col2:
    st.info("""
    **Rules Applied:**
    - **Rally Leaders:** Automatically ignored (top-right name).
    - **Active Members:** Highlighted names are recorded.
    - **Absent Members:** Greyed-out names are marked as `(ABSENT)`.
    - **Data Export:** All matches combined into one clean CSV.
    """)

# --- 5. PROCESSING LOGIC ---
if uploaded_files:
    if st.button("🚀 Start Processing Rally Attendance"):
        all_columns = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, file in enumerate(uploaded_files):
            file_name = file.name.split('.')[0]
            status_text.text(f"⚔️ Analyzing: {file_name}...")
            
            try:
                img = Image.open(file)
                img.thumbnail((1200, 1200)) 
                
                # Refined Prompt for 2026 Vision Models
                prompt = """
                Analyze the 'Manage Rally' UI in this screenshot:
                1. Focus ONLY on the list of members in the rally box.
                2. IGNORE the Rally Leader (the name at the top right next to the flag).
                3. EXTRACT all other player IGNs.
                4. For bright/highlighted names, return: 'Name'.
                5. For darkened/greyed-out names, return: 'Name (ABSENT)'.
                6. Return a plain list, one per line. No headers or markdown.
                """
                
                response = model.generate_content([prompt, img])
                names = [n.strip() for n in response.text.strip().split('\n') if n.strip()]
                
                all_columns[file_name] = names
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
            except Exception as e:
                st.error(f"Error in {file.name}: {e}")

        # --- 6. DATA DISPLAY & DOWNLOAD ---
        if all_columns:
            status_text.success(f"✅ Processed {len(uploaded_files)} rally reports!")
            
            # Create DataFrame
            df = pd.DataFrame.from_dict(all_columns, orient='index').transpose()
            
            st.divider()
            st.subheader("📊 Consolidated Attendance Report")
            st.dataframe(df, use_container_width=True)
            
            # Export CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
            
            st.download_button(
                label="📥 Download Combined CSV",
                data=csv_buffer.getvalue(),
                file_name="guild_rally_report.csv",
                mime="text/csv"
            )

# --- 7. FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("System Status: Operational")
st.sidebar.caption("Model: Gemini 3 Flash • 2026")
