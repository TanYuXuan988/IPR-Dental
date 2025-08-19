import streamlit as st
import datetime
import gspread
import pandas as pd

# -----------------------
# Initialize ALL Session State Variables
# -----------------------
if 'page' not in st.session_state:
    # Authentication
    st.session_state.page = "login"
    st.session_state.authenticated = False
    st.session_state.username = ""
    
    # Patient Data
    st.session_state.patient_data = {
        "name": "",
        "age": 0,
        "sex": "",
        "date": datetime.date.today(),
        "xray": None
    }

# Default credentials
DEFAULT_CREDENTIALS = {"UserIPR": "AdminIPR"}

# -----------------------
# Google Sheets Access (Simplified)
# -----------------------
def get_sheet(sheet_name):
    try:
        # Public sheet access
        gc = gspread.Client(auth={'api_key': st.secrets["public_api_key"]})
        return gc.open("IPR Login Logsheet").worksheet(sheet_name)
    except:
        return None

# -----------------------
# Authentication
# -----------------------
def verify_login(username, password):
    # 1. Try default credentials
    if username in DEFAULT_CREDENTIALS and DEFAULT_CREDENTIALS[username] == password:
        log_login(username, True)
        return True
        
    # 2. Try Google Sheets
    sheet = get_sheet("Credentials")
    if sheet:
        try:
            records = sheet.get_all_records()
            for record in records:
                if record['Username'] == username and record['Password'] == password:
                    log_login(username, True)
                    return True
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
# Page: Login
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
# Page: Patient Input
# -----------------------
elif st.session_state.page == "input" and st.session_state.authenticated:
    st.title("🦷 Dental X-ray Report - Step 1")
    
    with st.sidebar:
        st.title("Settings")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.rerun()
    
    # Patient Form - Access initialized session state safely
    st.header("Patient Information")
    st.session_state.patient_data["name"] = st.text_input(
        "Name", 
        value=st.session_state.patient_data["name"]
    )
    st.session_state.patient_data["age"] = st.number_input(
        "Age", 
        min_value=0, 
        max_value=120, 
        value=st.session_state.patient_data["age"]
    )
    st.session_state.patient_data["sex"] = st.selectbox(
        "Gender", 
        ["Male", "Female", "Other"],
        index=["Male", "Female", "Other"].index(st.session_state.patient_data["sex"]) if st.session_state.patient_data["sex"] else 0
    )
    st.session_state.patient_data["date"] = st.date_input(
        "Examination Date", 
        value=st.session_state.patient_data["date"]
    )
    
    st.header("Upload Dental X-ray")
    uploaded_file = st.file_uploader("Choose a bitewing X-ray", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.session_state.patient_data["xray"] = uploaded_file
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        if st.button("Next ➡️"):
            st.session_state.page = "summary"
            st.rerun()

# -----------------------
# Page: Summary
# -----------------------
elif st.session_state.page == "summary" and st.session_state.authenticated:
    st.title("📋 Dental X-ray Report Summary")
    
    with st.sidebar:
        st.title("Settings")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.page = "login"
            st.rerun()
    
    st.subheader("Patient Details")
    st.write(f"**Name:** {st.session_state.patient_data['name']}")
    st.write(f"**Age:** {st.session_state.patient_data['age']}")
    st.write(f"**Gender:** {st.session_state.patient_data['sex']}")
    st.write(f"**Examination Date:** {st.session_state.patient_data['date'].strftime('%B %d, %Y')}")
    
    st.subheader("Uploaded X-ray Image")
    if st.session_state.patient_data["xray"]:
        st.image(st.session_state.patient_data["xray"], use_column_width=True)
    
    if st.button("⬅️ Back"):
        st.session_state.page = "input"
        st.rerun()
