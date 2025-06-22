import streamlit as st

st.set_page_config(page_title="Boardroom", layout="centered", page_icon="🔵")

MAIN_BLUE = "#228be6"
SUBTEXT_BLUE = "#1864ab"
LIGHT_BG = "#f7faff"

# Hide sidebar on all pages
st.markdown(f"""
    <style>
        [data-testid="stSidebar"], .css-1d391kg, section[data-testid="stSidebar"] {{ display: none !important; }}
        .block-container {{ padding-top: 2rem; }}
        .main-header {{ color: {MAIN_BLUE} !important; font-weight: 700; text-align:center; }}
        .main-blue {{ color: {MAIN_BLUE} !important; }}
        .main-blue-bg {{ background: {LIGHT_BG} !important; }}
        .stButton > button {{ display: block; margin: 1.5em auto 0 auto !important; }}
    </style>
""", unsafe_allow_html=True)

# Only allow access if access_granted is exactly True
if st.session_state.get('access_granted', None) is not True:
    import time
    countdown_placeholder = st.empty()
    st.markdown(f"""
    <div style='display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:60vh;'>
        <h1 class='main-header'>Access Denied</h1>
        <div style='color:#e74c3c; font-size:1.2em; margin-bottom:2em;'>You must verify first to enter the boardroom.</div>
        <form action="/verify">
            <button type="submit" style='background:{MAIN_BLUE}; color:#fff; border:none; border-radius:8px; padding:0.7em 2em; font-size:1.1em; cursor:pointer;'>Go to Verification</button>
        </form>
    </div>
    """, unsafe_allow_html=True)
    for i in range(5, 0, -1):
        countdown_placeholder.markdown(f"<div style='margin-top:1.5em; color:#888; text-align:center;'>Redirecting to verification in {i} second{'s' if i > 1 else ''}...</div>", unsafe_allow_html=True)
        time.sleep(1)
    st.switch_page("pages/verify.py")
    st.stop()
else:
    st.markdown(f"""
    <div style='display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:60vh;'>
        <h1 class='main-header'>Boardroom - {st.session_state.get('persona_name', 'Guest')}</h1>
        <div style='background:{LIGHT_BG}; border-radius:16px; padding:2em 4em; box-shadow:0 2px 16px #0001; margin-top:2em; text-align:center;'>
            <h2 class='main-blue'>Zoom Meeting Room</h2>
            <div style='margin:2em 0;'>
                <img src='https://img.icons8.com/ios-filled/100/{MAIN_BLUE[1:]}/video-conference.png' width='100' style='margin:auto;'/>
            </div>
            <p style='color:#222;'>This is a dummy boardroom screen.<br>Video, audio, and chat features would appear here.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Leave Boardroom"):
        st.session_state['access_granted'] = None
        st.session_state['persona_name'] = None
        st.session_state['uploaded_selfie'] = None  # Clear uploaded selfie on leave
        st.switch_page("pages/verify.py")
