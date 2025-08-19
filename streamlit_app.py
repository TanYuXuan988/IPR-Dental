import streamlit as st
from PIL import Image
import datetime
import gspread
import pandas as pd

# -----------------------
# Configuration
# -----------------------
st.set_page_config(page_title="Dental Report", layout="centered")

# Initialize Google Sheets
def init_gsheets():
    try:
        gc = gspread.service_account(filename='.streamlit/secrets.toml')
        return gc
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        return None

# -----------------------
# Session State
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "login"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# -----------------------
# Page 1: Login
# -----------------------
if st.session_state.page == "login":
    st.title("🔐 Login to Dental Report System")
    
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if user == "UserIPR" and pwd == "AdminIPR":
            st.session_state.authenticated = True
            st.session_state.page = "input"
            st.success("Login successful ✅")
        else:
            st.error("Invalid credentials ❌")

# -----------------------
# Page 2: Patient Input
# -----------------------
elif st.session_state.page == "input" and st.session_state.authenticated:
    st.title("🦷 Dental X-ray Report - Step 1")
    
    # Sidebar
    st.sidebar.title("Settings")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.page = "login"
    
    # Patient Info
    st.header("Patient Information")
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, max_value=120)
    sex = st.selectbox("Gender", ["Male", "Female", "Other"])
    date = st.date_input("Examination Date", value=datetime.date.today())
    
    # File Upload
    st.header("Upload Dental X-ray")
    uploaded_file = st.file_uploader("Choose a bitewing X-ray", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        st.button("Next ➡️", on_click=lambda: st.session_state.update(page="summary"))

# -----------------------
# Page 3: Summary
# -----------------------
elif st.session_state.page == "summary" and st.session_state.authenticated:
    st.title("📋 Dental X-ray Report Summary")
    
    # Save to Google Sheets
    gc = init_gsheets()
    if gc:
        try:
            sheet = gc.open("DentalReports").sheet1
            sheet.append_row([
                st.session_state.name,
                st.session_state.age,
                st.session_state.sex,
                str(st.session_state.date)
            ])
            st.success("Data saved to Google Sheets!")
        except Exception as e:
            st.error(f"Couldn't save to Sheets: {e}")
    
    # Display summary
    st.subheader("Patient Details")
    st.write(f"Name: {st.session_state.name}")
    st.write(f"Age: {st.session_state.age}")
    st.write(f"Gender: {st.session_state.sex}")
    st.write(f"Date: {st.session_state.date.strftime('%Y-%m-%d')}")
    
    st.button("⬅️ Back", on_click=lambda: st.session_state.update(page="input"))
