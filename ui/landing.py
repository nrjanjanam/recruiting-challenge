import streamlit as st

st.set_page_config(page_title="Welcome to Validia Boardroom", layout="centered", page_icon="🟦")

MAIN_BLUE = "#228be6"
SUBTEXT_BLUE = "#1864ab"
LIGHT_BG = "#f7faff"

# Hide sidebar on landing page
st.markdown(f"""
    <style>
        [data-testid="stSidebar"], .css-1d391kg {{ display: none !important; }}
        .block-container {{ padding-top: 2rem; }}
        .main-header {{ color: {MAIN_BLUE} !important; font-weight: 700; text-align:center; }}
        .main-blue {{ color: {MAIN_BLUE} !important; }}
        .main-blue-bg {{ background: {LIGHT_BG} !important; }}
        .stButton > button {{ display: block; margin: 1.5em auto 0 auto !important; }}
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style='display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:60vh;'>
    <h1 class='main-header'>Welcome to Validia Secure Boardroom Platform</h1>
    <div style='text-align:center; font-size:1.2em; color:#222; margin-bottom:2em;'>
        Experience next-generation biometric authentication for your virtual meetings.<br>
        Seamlessly verify your identity and access secure boardrooms with confidence.
    </div>
    <div style='display:flex; flex-direction:column; align-items:center; justify-content:center;'>
        <img src='https://img.icons8.com/ios-filled/200/{MAIN_BLUE[1:]}/meeting-room.png' width='120' style='margin:auto;'/>
    </div>
</div>
""", unsafe_allow_html=True)

if st.button("Enroll", use_container_width=True):
    st.switch_page("pages/enroll.py")

if st.button("Start Verification", use_container_width=True):
    st.switch_page("pages/verify.py")

st.markdown("""
<hr style='margin:2em 0; width:100%; border:1px solid #eee;'>
<div style='font-size:0.95em; color:#888; text-align:center;'>Validia Boardroom is designed for privacy, compliance, and ease of use.</div>
""", unsafe_allow_html=True)
