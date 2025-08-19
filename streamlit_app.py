import streamlit as st
from PIL import Image
import datetime
import gspread
import pandas as pd

# -----------------------
# App Configuration
# -----------------------
st.set_page_config(page_title="Dental Report", layout="centered")

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "login"
    st.session_state.authenticated = False

# -----------------------
# Google Sheets Setup
# -----------------------
def init_gsheets():
    try:
        # Using direct API key authentication
        gc = gspread.Client(auth={'api_key': st.secrets["gsheets_api_key"]})
        return gc
    except Exception as e:
        st.error(f"Google Sheets connection failed: {str(e)}")
        return None

# -----------------------
# Authentication Functions
# -----------------------
def verify_login(username, password):
    gc = init_gsheets()
    if gc:
        try:
            sheet = gc.open("IPR Login Logsheet").worksheet("Credentials")
            records = sheet.get_all_records()
            for record in records:
                if record['Username'] == username and record['Password'] == password:
                    log_login(username, True)
                    return True
            log_login(username, False)
            return False
        except Exception as e:
            st.error(f"Login verification failed: {str(e)}")
            return False

def log_login(username, success):
    gc = init_gsheets()
    if gc:
        try:
            sheet = gc.open("IPR Login Logsheet").worksheet("Login Logs")
            sheet.append_row([
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                username,
                "Success" if success else "Failed"
            ])
        except Exception as e:
            st.error(f"Failed to log login attempt: {str(e)}")

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
            st.success("Login successful ✅")
        else:
            st.error("Invalid username or password ❌")

# -----------------------
# Page 2: Patient Input
# -----------------------
elif st.session_state.page == "input" and st.session_state.authenticated:
    st.title("🦷 Dental X-ray Report - Step 1")
    
    st.sidebar.title("⚙️ Settings")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.page = "login"
    
    st.header("👤 Patient Information")
    name = st.text_input("Name", key="name")
    age = st.number_input("Age", min_value=0, max_value=120, key="age")
    sex = st.selectbox("Gender", ["Male", "Female", "Other"], key="sex")
    date = st.date_input("Examination Date", key="date", value=datetime.date.today())
    
    st.header("📸 Upload Dental X-ray")
    uploaded_file = st.file_uploader("Upload a bitewing X-ray", type=["jpg", "jpeg", "png"], key="xray")
    
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        st.button("Next ➡️", on_click=lambda: st.session_state.update(page="summary"))

# -----------------------
# Page 3: Summary
# -----------------------
elif st.session_state.page == "summary" and st.session_state.authenticated:
    st.title("📋 Dental X-ray Report Summary")
    
    st.sidebar.title("⚙️ Settings")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.page = "login"
    
    st.subheader("Patient Details")
    st.write(f"**Name:** {st.session_state.name}")
    st.write(f"**Age:** {st.session_state.age}")
    st.write(f"**Gender:** {st.session_state.sex}")
    st.write(f"**Examination Date:** {st.session_state.date.strftime('%B %d, %Y')}")
    
    st.subheader("Uploaded X-ray Image")
    st.image(st.session_state.xray, use_column_width=True)
    
    st.button("⬅️ Back", on_click=lambda: st.session_state.update(page="input"))
