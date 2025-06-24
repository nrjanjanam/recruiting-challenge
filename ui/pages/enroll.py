import streamlit as st
import requests
import cv2
import numpy as np
import base64
import time

st.set_page_config(page_title="Enroll Face Profile", layout="centered", page_icon="🟦")

MAIN_BLUE = "#228be6"
LIGHT_BG = "#f7faff"
POSES = ["frontal", "left", "right", "up", "down"]

# --- Pose wheel state ---
if "pose_buckets" not in st.session_state or set(st.session_state.pose_buckets.keys()) != set(POSES):
    st.session_state.pose_buckets = {pose: False for pose in POSES}

# Hide sidebar and hamburger menu for a clean UI (move to very top for immediate effect)
st.markdown(f"""
    <style>
        [data-testid="stSidebar"], [data-testid="stSidebarNav"], .css-1d391kg, section[data-testid="stSidebar"], header[data-testid="stHeader"] {{ display: none !important; }}
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
    </style>
""", unsafe_allow_html=True)

# --- Metadata input before selfies ---
with st.form(key="enroll_metadata_form", clear_on_submit=False):
    name = st.text_input("Name (required)", value=st.session_state.get("enroll_name", ""))
    submitted = st.form_submit_button("Continue to Selfie Capture")
    if submitted:
        if not name.strip():
            st.warning("Name is required to proceed.")
            st.stop()
        st.session_state["enroll_name"] = name

if "enroll_name" not in st.session_state or not st.session_state["enroll_name"].strip():
    st.stop()

# --- Guided pose capture and QC using st.camera_input ---
for pose in POSES:
    if not isinstance(st.session_state.pose_buckets[pose], np.ndarray):
        if pose == "frontal":
            st.write("Capture frontal pose (look straight at the camera)")
        elif pose == "left":
            st.write("Capture left pose (turn your face slightly left, but not more than 30°)")
        elif pose == "right":
            st.write("Capture right pose (turn your face slightly right, but not more than 30°)")
        elif pose == "up":
            st.write("Capture up pose (tilt your head up, but not more than 30°)")
        elif pose == "down":
            st.write("Capture down pose (tilt your head down, but not more than 30°)")
        camera_image = st.camera_input(
            label=f"Take a {pose} selfie",
            key=f"camera_{pose}",
            help=f"Capture a clear {pose} pose using your webcam."
        )
        if camera_image:
            file_bytes = np.asarray(bytearray(camera_image.getvalue()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            rgb = img[:, :, ::-1]
            # QC call for this pose (pose check is handled by backend, but user is guided only)
            res = requests.post(f"http://localhost:8000/enroll/qc/{pose}", files={"frame": (f"{pose}.jpg", cv2.imencode(".jpg", rgb[..., ::-1])[1].tobytes(), "image/jpeg")}).json()
            if res.get("ok"):
                st.session_state.pose_buckets[pose] = rgb
                st.success(f"{pose.capitalize()} accepted!")
                st.rerun()
            else:
                st.warning(f"{pose.capitalize()} rejected – {res.get('reason','QC failed')}")
        st.stop()

# --- Enroll once all five accepted ---
if all(isinstance(st.session_state.pose_buckets[p], np.ndarray) for p in POSES):
    frames_dict = {p: st.session_state.pose_buckets[p].tolist() for p in POSES}
    try:
        r = requests.post(
            "http://localhost:8000/v1/profile-create-5poses",
            json={
                "frames": frames_dict,
                "name": st.session_state["enroll_name"],
                # Optionally add user_id, extra here if desired
            }
        )
        if r.ok:
            st.success("Profile created successfully! Redirecting to landing page...")
            time.sleep(5)
            st.switch_page("landing.py")
        else:
            st.error(f"Enroll failed: {r.text}")
    except Exception as e:
        st.error(f"Failed to enroll: {e}")

# --- Pose-wheel colouring ---
segments = ''.join([
    f'<div class="pose-segment {"filled" if isinstance(st.session_state.pose_buckets[p], np.ndarray) else ""}">{p[0].upper()}</div>'
    for p in POSES])
st.markdown(f'<div class="pose-wheel">{segments}</div>', unsafe_allow_html=True)
