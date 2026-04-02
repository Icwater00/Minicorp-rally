import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Guild Rally Attendance",
    page_icon="⚔️",
    layout="wide"
)

# Custom CSS to make it look "Gaming" oriented
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    ststButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #2ecc71;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURITY & API SETUP ---
# This pulls from the "Secrets" tab in Streamlit Cloud
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
    else:
        # Fallback for local testing (only if you have a secrets.toml)
        API_KEY = st.sidebar.text_input("Enter API Key manually", type="password")
    
    if API_KEY:
        genai.configure(api_key=API_KEY)
        # Using Gemini 3 Flash for 2026 speed/accuracy
        model = genai.GenerativeModel('gemini-3-flash-preview')
    else:
        st.warning("⚠️ API Key missing. Please configure it in Streamlit Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# --- 3. UI HEADER ---
st.title("⚔️ Guild Rally Attendance Portal")
st.write("Upload screenshots of the **Manage Rally** screen to automatically generate a report.")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_files = st.file_uploader(
        "Drop Rally Screenshots Here", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )

with col2:
    st.info("""
    **Instructions:**
    1. Upload one or more screenshots.
    2. The AI will look only at the **Manage Rally** box.
    3. Greyed-out names will be marked as **ABSENT**.
    4. Download the final CSV for your records.
    """)

# --- 4. PROCESSING LOGIC ---
if uploaded_files:
    if st.button("🚀 Process Rally Attendance"):
        all_columns = {}
        
        # UI Progress elements
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Iterate through uploaded files
        for idx, file in enumerate(uploaded_files):
            file_name = file.name.split('.')[0]
            status_text.text(f"Analyzing Match: {file_name}...")
            
            try:
                # Open image and resize for faster processing
                img = Image.open(file)
                img.thumbnail((1200, 1200)) 
                
                # The precise prompt for your game UI
                prompt = """
                Look ONLY at the 'Manage Rally' box in this screenshot.
                1. Extract player names that are highlighted or bright (Active players).
                2. If a name is darkened or greyed out (like 'SCIPIO'), mark them as 'ABSENT'.
                3. Ignore all other background text, stats, or UI buttons.
                4. Return a plain list of names. 
                   Format: 'Name' (for active) or 'Name (ABSENT)' (for greyed out).
                5. One name per line. No extra text.
                """
                
                response = model.generate_content([prompt, img])
                
                # Clean and split the response into a list
                names = [n.strip() for n in response.text.strip().split('\n') if n.strip()]
                
                # Map names to the filename column
                all_columns[file_name] = names
                
                # Update progress bar
                progress_bar.progress((idx + 1) / len(uploaded_files))
                
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")

        # --- 5. RESULTS DISPLAY ---
        if all_columns:
            status_text.success(f"Successfully processed {len(uploaded_files)} images!")
            
            # Create DataFrame (pandas handles mismatched row counts automatically)
            df = pd.DataFrame.from_dict(all_columns, orient='index').transpose()
            
            st.divider()
            st.subheader("📊 Combined Attendance Table")
            st.dataframe(df, use_container_width=True)
            
            # Prepare CSV for download
            csv_buffer = io.StringIO()
            # utf-8-sig ensures Excel opens symbols like 'シ' correctly
            df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label="📥 Download Attendance CSV",
                data=csv_data,
                file_name="rally_attendance_report.csv",
                mime="text/csv"
            )

# --- 6. FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("Powered by Gemini 3 Flash • 2026")