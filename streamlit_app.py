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

# =============================
# class colors
# =============================
CLASS_COLORS = {
    "caries": (255, 0, 0),                      # Red
    "infection": (255, 255, 0),                 # Orange
    "impacted": (0, 0, 255),                    # Blue
    "fractured": (255, 255, 0),                 # Yellow
    "broken_down_crown_root": (255, 0, 255),    # Purple
    "healthy": (0, 255, 0),                     # Green
}

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
        "annotated_image": None,
        "confidence_threshold": 0.5
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
# load YOLOv8s model
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

def run_yolo(image, conf_thresh=0.5):
    results = model(image)
    detections = []
    boxes = getattr(results[0], "boxes", None)

    image_copy = np.array(image).copy()

    if boxes:
        for b in boxes:
            conf = float(getattr(b, "conf", 0))
            if conf < conf_thresh:
                continue
            cls = int(getattr(b, "cls", -1))
            name = model.names.get(cls, str(cls)) if hasattr(model, "names") else str(cls)
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            color = CLASS_COLORS.get(name, (0, 255, 0))
            cv2.rectangle(image_copy, (x1, y1), (x2, y2), color, 2)
            cv2.putText(image_copy, f"{name} {conf:.2f}", (x1, max(20, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            detections.append({"Object": name, "Confidence": f"{conf:.2f}"})

    annotated = Image.fromarray(image_copy)
    return annotated, detections

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
                "annotated_image": None,
            })
            st.rerun()
        else:
            st.error("Invalid username or password ❌")

def input_page():
    st.title("🦷 Dental X-ray Report")

    with st.sidebar:
        st.title("⚙️ Settings")
        st.write("Confidence Threshold")
        st.session_state.confidence_threshold = st.selectbox(
            "Select minimum detection confidence",
            [0.0, 0.5, 0.6, 0.7, 0.8, 0.9],
            index=[0.0, 0.5, 0.6, 0.7, 0.8, 0.9].index(st.session_state.confidence_threshold)
        )
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
        st.write(f" **Aspect ratio:** {aspect_ratio:.2f}")
        st.write(f" **Grayscale check:** {'✅ Passed' if grayscale_ok else '❌ Failed'}")

        if panoramic_ok and grayscale_ok:
            st.success("✅ Image is a valid panoramic dental X-ray.")
            st.session_state.xray = image

            if st.button("Run Detection"):
                with st.spinner("Running YOLOv8s detection..."):
                    annotated, detections = run_yolo(image, st.session_state.confidence_threshold)
                    st.session_state.annotated_image = annotated
                    st.session_state.detection_results = detections
                    st.session_state.page = "summary"
                    st.rerun()
        else:
            # error messages
            if not panoramic_ok and not grayscale_ok:
                st.error("🚫 This image failed both checks — it is not panoramic and it’s not in grayscale.")
            elif not panoramic_ok:
                st.error("⚠️ The aspect ratio is outside the expected range for a panoramic dental X-ray.")
            elif not grayscale_ok:
                st.error("⚠️ This image is not grayscale like a typical panoramic X-ray.")

def summary_page():
    st.title("📋 Dental X-ray Report Summary")

    with st.sidebar:
        st.title("⚙️ Settings")
        st.write("Confidence Threshold")
        st.session_state.confidence_threshold = st.selectbox(
            "Select minimum detection confidence",
            [0.0, 0.5, 0.6, 0.7, 0.8, 0.9],
            index=[0.0, 0.5, 0.6, 0.7, 0.8, 0.9].index(st.session_state.confidence_threshold)
        )
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
    if st.session_state.annotated_image:
        annotated, detections = run_yolo(st.session_state.xray, st.session_state.confidence_threshold)
        st.session_state.annotated_image = annotated
        st.session_state.detection_results = detections

        st.image(st.session_state.annotated_image, use_column_width=True)
        if st.session_state.detection_results:
            df = pd.DataFrame(st.session_state.detection_results)
            st.table(df)
        buf = io.BytesIO()
        st.session_state.annotated_image.save(buf, format="PNG")
        buf.seek(0)
        st.download_button("Download Annotated Image", data=buf, file_name="detection.png", mime="image/png")

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
