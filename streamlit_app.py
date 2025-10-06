# =============================
# imports
# =============================
import os
import datetime
import streamlit as st
import numpy as np
import io
import pandas as pd
import cv2
from ultralytics import YOLO
from PIL import Image

# =============================
# config
# =============================
DEFAULT_CREDENTIALS = {"UserIPR": "AdminIPR"}
MODEL_PATH = "best.pt"
ASPECT_MIN = 1.3
ASPECT_MAX = 2.6

# Initialize session state variables
if "annotated_image" not in st.session_state:
    st.session_state.annotated_image = None
if "detection_results" not in st.session_state:
    st.session_state.detection_results = None
if "xray" not in st.session_state:
    st.session_state.xray = None
if "confidence_threshold" not in st.session_state:
    st.session_state.confidence_threshold = 0.5

# =============================
# initialize session
# =============================
def init_session_state():
    defaults = {
        "page": "login",
        "authenticated": False,
        "username": "",
        "name": "",
        "age": 0,
        "sex": "",
        "date": datetime.date.today(),
        "xray": None,
        "detection_results": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# =============================
# authentication
# =============================
def verify_login(username, password):
    return DEFAULT_CREDENTIALS.get(username) == password

# =============================
# load YOLOv8 model
# =============================
@st.cache_resource
def load_model(path):
    return YOLO(path)

model = load_model(MODEL_PATH)

# =============================
# helper functions
# =============================
def is_panoramic(image):
    width, height = image.size
    aspect_ratio = width / height if height != 0 else 0
    return ASPECT_MIN <= aspect_ratio <= ASPECT_MAX, aspect_ratio

def is_grayscale(image, threshold=10):
    img_np = np.array(image)
    if len(img_np.shape) < 3 or img_np.shape[2] == 1:
        return True
    std = np.std(img_np[:, :, :3], axis=2)
    mean_std = np.mean(std)
    return mean_std < threshold

def is_panoramic_xray(image):
    panoramic_ok, aspect_ratio = is_panoramic(image)
    grayscale_ok = is_grayscale(image)
    return panoramic_ok, aspect_ratio, grayscale_ok

def run_yolo(image):
    """Run YOLO once and store raw detection info."""
    results = model(image)
    boxes = getattr(results[0], "boxes", None)
    detections = []

    if boxes:
        for b in boxes:
            conf = float(getattr(b, "conf", 0))
            cls = int(getattr(b, "cls", -1))
            xyxy = b.xyxy[0].tolist() if hasattr(b, "xyxy") else [0, 0, 0, 0]
            name = model.names.get(cls, str(cls)) if hasattr(model, "names") else str(cls)
            detections.append({
                "Object": name,
                "Confidence": conf,
                "Box": xyxy
            })
    return detections

# =============================
# pages
# =============================
def login_page():
    st.title("🔐 Login to Dental Report System")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_login(username, password):
            st.session_state.update({
                "authenticated": True,
                "username": username,
                "page": "input",
                "name": "",
                "age": 0,
                "sex": "",
                "date": datetime.date.today(),
                "xray": None,
                "detection_results": None,
            })
            st.rerun()
        else:
            st.error("Invalid username or password ❌")

def input_page():
    st.title("🦷 Dental X-ray Report")

    with st.sidebar:
        st.title("⚙️ Settings")
        if st.button("Logout"):
            st.session_state.update({"authenticated": False, "page": "login"})
            st.rerun()

    st.header("👤 Patient Information")
    st.session_state.name = st.text_input("Name", value=st.session_state.name)
    st.session_state.age = st.number_input("Age", min_value=0, max_value=120, value=st.session_state.age)
    st.session_state.sex = st.selectbox(
        "Gender", ["Male", "Female", "Other"],
        index=["Male", "Female", "Other"].index(st.session_state.sex) if st.session_state.sex else 0
    )
    st.session_state.date = st.date_input("Examination Date", value=st.session_state.date)

    st.header("📸 Upload Panoramic Dental X-ray")
    uploaded_file = st.file_uploader("Upload a panoramic Dental X-ray", type=["jpg", "jpeg", "png"])

    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        panoramic_ok, aspect_ratio, grayscale_ok = is_panoramic_xray(image)

        # show preview
        st.image(image, caption="Uploaded Image Preview", use_column_width=True)
        st.write(f"**Aspect ratio:** {aspect_ratio:.2f}")
        st.write(f"**Grayscale check:** {'✅ Passed' if grayscale_ok else '❌ Failed'}")

        if panoramic_ok and grayscale_ok:
            st.success("✅ Image is a valid panoramic dental X-ray.")
            st.session_state.xray = image

            if st.button("Run Detection"):
                with st.spinner("Running YOLOv8s detection..."):
                    detections = run_yolo(image)
                    st.session_state.detection_results = detections
                    st.session_state.page = "summary"
                    st.rerun()
        else:
            # detailed error messages
            if not panoramic_ok and not grayscale_ok:
                st.error("🚫 Failed both checks — not panoramic and not grayscale.")
            elif not panoramic_ok:
                st.error("⚠️ Aspect ratio outside panoramic range.")
            elif not grayscale_ok:
                st.error("⚠️ Image is not grayscale like a typical panoramic X-ray.")

def summary_page():
    st.title("📋 Dental X-ray Report Summary")

    with st.sidebar:
        st.title("⚙️ Settings")
        if st.button("Logout"):
            st.session_state.update({"authenticated": False, "page": "login"})
            st.rerun()

    st.subheader("Patient Details")
    st.write(f"**Name:** {st.session_state.name}")
    st.write(f"**Age:** {st.session_state.age}")
    st.write(f"**Gender:** {st.session_state.sex}")
    st.write(f"**Examination Date:** {st.session_state.date.strftime('%B %d, %Y')}")

    st.subheader("Uploaded X-ray Image")
    if st.session_state.xray:
        st.image(st.session_state.xray, use_column_width=True)

    st.subheader("YOLOv8s Detection Results")
    if st.session_state.annotated_image and st.session_state.detection_results:
        # confidence filter slider (below annotated image)
        st.image(st.session_state.annotated_image, use_column_width=True)
        threshold = st.slider(
            "Confidence Threshold",
            0.5, 0.9, 0.5, 0.1,
            help="Filter detections below this confidence level."
        )

        # Filter detection results
        df = pd.DataFrame(st.session_state.detection_results)
        df["Confidence"] = df["Confidence"].astype(float)
        filtered_df = df[df["Confidence"] >= threshold]

        st.subheader(f"Filtered Results (≥ {threshold:.1f})")
        if len(filtered_df) > 0:
            st.table(filtered_df)
        else:
            st.info("No detections above this confidence threshold.")

        # Download button for annotated image
        buf = io.BytesIO()
        st.session_state.annotated_image.save(buf, format="PNG")
        buf.seek(0)
        st.download_button(
            "📥 Download Annotated Image",
            data=buf,
            file_name="detection.png",
            mime="image/png"
        )

    if st.button("⬅️ Back"):
        st.session_state.page = "input"
        st.rerun()


# =============================
# page navigation
# =============================
init_session_state()

if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "input" and st.session_state.authenticated:
    input_page()
elif st.session_state.page == "summary" and st.session_state.authenticated:
    summary_page()
