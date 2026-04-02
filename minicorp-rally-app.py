import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io
from concurrent.futures import ThreadPoolExecutor

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="High-Speed Guild OCR", page_icon="⚡", layout="wide")

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
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTH & API ---
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

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-3-flash-preview')
except:
    st.error("API Key missing in Secrets.")
    st.stop()

# --- 3. HELPER FUNCTION FOR PARALLEL WORK ---
def process_single_image(file):
    """Worker function to handle one image upload"""
    try:
        img = Image.open(file)
        img.thumbnail((1200, 1200)) # Optimization: Resize before sending
        
        prompt = """
        Analyze the 'Manage Rally' UI:
        1. IGNORE the name at the very top-right corner (header label).
        2. EXTRACT all player names found INSIDE the scrollable list area.
        3. Include names in the list even if they match the top-right header.
        4. For bright names: 'Name'. For greyed-out: 'Name (ABSENT)'.
        Return a plain list, one name per line.
        """
        
        response = model.generate_content([prompt, img])
        return file.name.split('.')[0], [n.strip() for n in response.text.strip().split('\n') if n.strip()]
    except Exception as e:
        return file.name, [f"Error: {str(e)}"]

# --- 4. UI ---
st.title("⚡ High-Speed Rally Attendance")
uploaded_files = st.file_uploader("Upload Screenshots", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 Collect now"):
        all_columns = {}
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        # --- THE SPEED FIX: Multi-threading ---
        # We process up to 5 images at once
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(process_single_image, uploaded_files))
            
            for idx, (file_name, names) in enumerate(results):
                all_columns[file_name] = names
                progress_bar.progress((idx + 1) / len(uploaded_files))

        if all_columns:
            st.success(f"✅ Finished {len(uploaded_files)} images in parallel!")
            df = pd.DataFrame.from_dict(all_columns, orient='index').transpose()
            df.index = df.index + 1 # Row 1 Start
            
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=True, index_label="Row", encoding="utf-8-sig")
            st.download_button("📥 Download Combined CSV", data=csv, file_name="fast_rally_report.csv")
