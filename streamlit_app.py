# ========================================
# Imports
# ========================================
import os
import datetime
import streamlit as st
from PIL import Image
import numpy as np
from ultralytics import YOLO
import io
import pandas as pd

# ========================================
# Config
# ========================================
DEFAULT_CREDENTIALS = {"UserIPR": "AdminIPR"}
MODEL_PATH = "best.pt"
ASPECT_MIN = 1.3
ASPECT_MAX = 2.6

# ========================================
# Session State Setup
# ========================================
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ========================================
# Authentication
# ========================================
def verify_login(username, password):
    return DEFAULT_CREDENTIALS.get(username) == password

# ========================================
# Load YOLO Model
# ========================================
def load_model(path):
    return YOLO(path)

try:
    model = load_model(MODEL_PATH)
except Exception as e:
    st.error(f"Failed to load YOLOv8s model at '{MODEL_PATH}': {e}")
    st.stop()

# ========================================
# Helper functions
# ========================================
def is_panoramic(image):
    """Check if the image is a panoramic dental X-ray based on aspect ratio."""
    width, height = image.size
    aspect_ratio = width / height if height != 0 else 0
    return ASPECT_MIN <= aspect_ratio <= ASPECT_MAX, aspect_ratio

def run_yolo(image):
    """Run YOLO inference and return annotated image + detections"""
    results = model(image)
    # Convert results[0].plot() to PIL.Image
    annotated = Image.fromarray(results[0].plot())
    # Extract detection table
    detections = []
    boxes = getattr(results[0], "boxes", None)
    if boxes:
        for b in boxes:
            conf = float(getattr(b, "conf", 0))
            cls = int(getattr(b, "cls", -1))
            name = model.names.get(cls, str(cls)) if hasattr(model, "names") else str(cls)
            detections.append({"Object": name, "Confidence": f"{conf:.2f}"})
    return annotated, detections

# ========================================
# Pages
# ========================================
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
    st.title("🦷 Dental X-ray Report - Step 1")
    
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
    uploaded_file = st.file_uploader("Upload a panoramic X-ray (jpg/png)", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        panoramic, aspect_ratio = is_panoramic(image)
        st.write(f"📐 Aspect ratio: {aspect_ratio:.2f}")
        if panoramic:
            st.success("✅ Image looks like a panoramic dental X-ray.")
            st.session_state.xray = image
            st.image(image, caption="Uploaded Panoramic X-ray", use_column_width=True)
            if st.button("Next ➡️"):
                # Run YOLO and store results in session
                annotated, detections = run_yolo(image)
                st.session_state.annotated_image = annotated
                st.session_state.detection_results = detections
                st.session_state.page = "summary"
                st.rerun()
        else:
            st.error("🚫 This does not appear to be a panoramic dental X-ray. Please upload a panoramic image.")

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
    if st.session_state.annotated_image:
        st.image(st.session_state.annotated_image, use_column_width=True)
        if st.session_state.detection_results:
            df = pd.DataFrame(st.session_state.detection_results)
            st.table(df)
        # Download button
        buf = io.BytesIO()
        st.session_state.annotated_image.save(buf, format="PNG")
        buf.seek(0)
        st.download_button("Download Annotated Image", data=buf, file_name="detection.png", mime="image/png")
    
    if st.button("⬅️ Back"):
        st.session_state.page = "input"
        st.rerun()

# ========================================
# Main App Router
# ========================================
init_session_state()

if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "input" and st.session_state.authenticated:
    input_page()
elif st.session_state.page == "summary" and st.session_state.authenticated:
    summary_page()
