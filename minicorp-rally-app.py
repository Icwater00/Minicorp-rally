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
    if "password_correct" not in st.session_state:
        st.title("🛡️ Guild Access Control")
        pwd = st.text_input("Enter Guild Member Password", type="password")
        if st.button("Unlock Portal"):
            if pwd == st.secrets.get("APP_PASSWORD", "admin123"): 
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
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-3-flash-preview')
    else:
        st.warning("⚠️ API Key missing. Please check Streamlit Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Config Error: {e}")
    st.stop()

# --- 4. UI HEADER ---
st.title("⚔️ Guild Rally Attendance Portal")
st.write("Extract rally participants. **Rally Leaders are filtered out from every page.**")

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
    - **No Duplicates:** The Rally Leader (top-right) is excluded from every match.
    - **Row Start:** Lists start at **Row 1**.
    - **Status:** Greyed-out members marked as `(ABSENT)`.
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
                
                # REFINED PROMPT: Explicitly filter out the Rally Leader from ALL extractions
                prompt = """
                Analyze the 'Manage Rally' window:
                1. Identify the 'Rally Leader' name (located at the top-right header next to the flag). 
                2. DO NOT include the Rally Leader in the final list.
                3. ONLY extract the names of the members listed in the main scrollable rally area.
                4. For bright/active names, return: 'Name'.
                5. For darkened/greyed-out names, return: 'Name (ABSENT)'.
                6. Return a plain list, one name per line. No extra text or symbols.
                """
                
                response = model.generate_content([prompt, img])
                names = [n.strip() for n in response.text.strip().split('\n') if n.strip()]
                
                all_columns[file_name] = names
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
            except Exception as e:
                st.error(f"Error in {file.name}: {e}")

        # --- 6. DATA DISPLAY & DOWNLOAD ---
        if all_columns:
            status_text.success(f"✅ Processed {len(uploaded_files)} matches!")
            
            # Create DataFrame
            df = pd.DataFrame.from_dict(all_columns, orient='index').transpose()
            
            # Row Offset Fix
            df.index = df.index + 1
            
            st.divider()
            st.subheader("📊 Consolidated Attendance Report")
            st.dataframe(df, use_container_width=True)
            
            # Export CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=True, index_label="Row", encoding="utf-8-sig")
            
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
