import streamlit as st
from PIL import Image
import requests
import datetime
import base64

# Load color config from Streamlit config.toml
MAIN_BLUE = "#228be6"
SUBTEXT_BLUE = "#1864ab"
ERROR_RED = "#e74c3c"
LIGHT_BG = "#f7faff"

API_URL = "http://127.0.0.1:8000/v1/verify-profile"

def verify_profile_api(uploaded_file):
    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
    response = requests.post(API_URL, files=files)
    return response.json()

st.set_page_config(page_title="Secure Boardroom Access", layout="centered", page_icon="🔐")

# Hide sidebar on all pages (force on first load too)
st.markdown(f"""
    <style>
        [data-testid="stSidebar"], .css-1d391kg, section[data-testid="stSidebar"] {{ display: none !important; }}
        .block-container {{ padding-top: 2rem; }}
        .stButton > button {{
            margin-bottom: 1.5em !important;
            margin-left: auto !important;
            margin-right: auto !important;
            margin-top: 1.5em !important;
            display: block !important;
        }}
        /* Add vertical gap between all widgets */
        .block-container > div:not(:last-child) {{
            margin-bottom: 1.5em !important;
        }}
        .custom-upload-area {{
            background: {LIGHT_BG};
            border-radius: 16px;
            box-shadow: 0 2px 16px {MAIN_BLUE}10;
            max-width: 400px;
            width: 100%;
            text-align: center;
            padding: 2em 2em 1em 2em;
            margin-bottom: 1.5em;
            border: 2px dashed {MAIN_BLUE};
        }}
        .custom-upload-label {{
            color: {MAIN_BLUE};
            font-size: 1.2em;
            margin-bottom: 1em;
            font-weight: 600;
        }}
        .uploaded-img {{
            border-radius: 12px;
            box-shadow: 0 2px 8px {MAIN_BLUE}10;
            margin-bottom: 1em;
            max-width: 100%;
        }}
        .stFileUploader > label {{ display: none; }}
        .access-denied {{
            border:2px solid {ERROR_RED};
            border-radius:12px;
            padding:1em;
            text-align:center;
            font-size:1.3em;
            color:{ERROR_RED};
            background:#fff;
            margin-bottom:1em;
        }}
        .main-blue {{
            color: {MAIN_BLUE} !important;
        }}
        .main-blue-bg {{
            background: {LIGHT_BG} !important;
        }}
        .main-blue-border {{
            border-color: {MAIN_BLUE} !important;
        }}
        .main-header {{
            color: {MAIN_BLUE} !important;
            font-weight: 700;
            margin-bottom: 2.5em !important;
        }}
        .main-subtext {{
            color: {SUBTEXT_BLUE} !important;
        }}
    </style>
""", unsafe_allow_html=True)

# Remove st.title and use a centered, styled header
st.markdown(f"""
<div style='display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:10vh;'>
    <h1 class='main-header' style='margin-bottom:0.2em;'>🔐 Secure Boardroom Access</h1>
    <div style='text-align:center; font-size:1.2em;' class='main-header'>
        Welcome to the secure boardroom. Please verify your identity to continue.
    </div>
</div>
""", unsafe_allow_html=True)

# --- Selfie Upload Area ---
selfie_col = st.container()
with selfie_col:
    # Show access denied message above the photo/upload area
    if 'access_granted' in st.session_state and st.session_state['access_granted'] is False:
        st.markdown(f"<div class='access-denied'>🔒 <b>Locked</b> — Access Denied.<br><span style='font-size:0.9em;color:{SUBTEXT_BLUE};'>Please try again.</span></div>", unsafe_allow_html=True)
    captured_selfie = st.session_state.get('captured_selfie', None)
    if not captured_selfie:
        # Use st.camera_input for webcam capture
        camera_image = st.camera_input(
            label="Take a selfie to verify",
            key="main_camera",
            help="Capture a clear selfie using your webcam."
        )
        if camera_image:
            st.session_state['captured_selfie'] = camera_image
            st.rerun()
    else:
        # Simpler, smaller preview area, centered
        img_bytes = captured_selfie.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode()
        st.markdown(f"""
        <div style='text-align:center;'>
            <div class='custom-upload-label' style='font-size:1.1em; margin-bottom:0.5em;'>Selfie Preview</div>
            <img src='data:image/png;base64,{img_b64}' width='180' style='display:block; margin:auto; border-radius:12px; box-shadow:0 2px 8px {MAIN_BLUE}10; margin-bottom:0;' />
        </div>
        """, unsafe_allow_html=True)
        # Remove Photo and Verify should be visually grouped
        col1, col2 = st.columns([1,1], gap="small")
        with col1:
            if st.button("Retake Photo", key="remove_selfie", use_container_width=True):
                st.session_state['captured_selfie'] = None
                st.session_state['access_granted'] = None  # Clear access denied/locked state
                st.rerun()
        with col2:
            if st.button("Verify", key="verify_photo", use_container_width=True):
                if not captured_selfie:
                    st.warning("Please take your selfie.")
                else:
                    api_result = verify_profile_api(captured_selfie)
                    probe_img = Image.open(captured_selfie)
                    # Defensive: handle missing or malformed API response
                    data = api_result.get("data", {}) if isinstance(api_result, dict) else {}
                    matched_profile = data.get("matched_profile")
                    persona_name = matched_profile.get('name', 'N/A') if matched_profile else "Unknown"
                    if api_result.get("success") and data.get("match"):
                        st.session_state['access_granted'] = True
                        st.session_state['persona_name'] = persona_name
                        st.switch_page("pages/boardroom.py")
                    else:
                        st.session_state['access_granted'] = False
                        st.rerun()
