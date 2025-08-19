import streamlit as st
import datetime
import gspread
from gspread_pandas import Spread, Client
import pandas as pd

# -----------------------
# Initialize Session State
# -----------------------
if 'page' not in st.session_state:
    st.session_state.page = "login"
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.patient_data = {
        "name": "",
        "age": 0,
        "sex": "",
        "date": datetime.date.today(),
        "xray": None
    }

# Default credentials (always works)
DEFAULT_CREDENTIALS = {"UserIPR": "AdminIPR"}

# -----------------------
# Google Sheets Access
# -----------------------
def get_sheet(sheet_name):
    try:
        # Method 1: Public sheet access (no auth needed)
        gc = gspread.Client(auth={'api_key': st.secrets["public_api_key"]})
        return gc.open("IPR Login Logsheet").worksheet(sheet_name)
    except:
        return None

# -----------------------
# Authentication
# -----------------------
def verify_login(username, password):
    # 1. Try default credentials first
    if username in DEFAULT_CREDENTIALS and DEFAULT_CREDENTIALS[username] == password:
        return True
        
    # 2. Try Google Sheets
    sheet = get_sheet("Credentials")
    if sheet:
        try:
            records = sheet.get_all_records()
            return any(r['Username'] == username and r['Password'] == password for r in records)
        except:
            pass
    return False

def log_login(username, success):
    sheet = get_sheet("Login Logs")
    if sheet:
        try:
            sheet.append_row([
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                username,
                "Success" if success else "Failed"
            ])
        except:
            pass
            
# ----------------------- 
# Page 1: Login
# -----------------------
if st.session_state.page == "login":
    st.title("🔐 Login to Dental Report System")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if verify_login(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.page = "input"
            st.rerun()
        else:
            st.error("Invalid username or password ❌")

# -----------------------
# Page 2: Patient Input
# -----------------------
elif st.session_state.page == "input" and st.session_state.authenticated:
    st.title("🦷 Dental X-ray Report - Step 1")
    
    with st.sidebar:
        st.title("⚙️ Settings")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.rerun()
    
    st.header("👤 Patient Information")
    st.session_state.name = st.text_input("Name", value=st.session_state.name)
    st.session_state.age = st.number_input("Age", min_value=0, max_value=120, value=st.session_state.age)
    st.session_state.sex = st.selectbox("Gender", ["Male", "Female", "Other"], index=0 if not st.session_state.sex else ["Male", "Female", "Other"].index(st.session_state.sex))
    st.session_state.date = st.date_input("Examination Date", value=st.session_state.date)
    
    st.header("📸 Upload Dental X-ray")
    uploaded_file = st.file_uploader("Upload a bitewing X-ray", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.session_state.xray = uploaded_file
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        if st.button("Next ➡️"):
            st.session_state.page = "summary"
            st.rerun()

# -----------------------
# Page 3: Summary
# -----------------------
elif st.session_state.page == "summary" and st.session_state.authenticated:
    st.title("📋 Dental X-ray Report Summary")
    
    with st.sidebar:
        st.title("⚙️ Settings")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.rerun()
    
    st.subheader("Patient Details")
    st.write(f"**Name:** {st.session_state.name}")
    st.write(f"**Age:** {st.session_state.age}")
    st.write(f"**Gender:** {st.session_state.sex}")
    st.write(f"**Examination Date:** {st.session_state.date.strftime('%B %d, %Y')}")
    
    st.subheader("Uploaded X-ray Image")
    if st.session_state.xray:
        st.image(st.session_state.xray, use_column_width=True)
    
    if st.button("⬅️ Back"):
        st.session_state.page = "input"
        st.rerun()
