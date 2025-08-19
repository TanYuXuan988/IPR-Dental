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
    st.session_state.username = "UserIPR"
    st.session_state.password = "AdminIPR"

# -----------------------
# Google Sheets Setup
# -----------------------
def init_gsheets():
    try:
        # Using direct API access (no service account)
        gc = gspread.oauth()  # Will prompt for authentication
        return gc
    except Exception as e:
        st.error(f"Google Sheets connection failed: {str(e)}")
        return None

# -----------------------
# Page: Login
# -----------------------
if st.session_state.page == "login":
    st.title("🔐 Dental Report Login")
    
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if user == st.session_state.username and pwd == st.session_state.password:
            st.session_state.authenticated = True
            st.session_state.page = "input"
            st.success("Login successful")
        else:
            st.error("Invalid credentials")

# -----------------------
# Page: Patient Input
# -----------------------
elif st.session_state.page == "input" and st.session_state.authenticated:
    st.title("🦷 New Patient Report")
    
    # Sidebar
    with st.sidebar:
        st.title("Settings")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.page = "login"
        
        # Password change
        with st.expander("Change Password"):
            old_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password", type="password")
            if st.button("Update"):
                if old_pwd == st.session_state.password:
                    st.session_state.password = new_pwd
                    st.success("Password updated")
                else:
                    st.error("Incorrect current password")
    
    # Patient Form
    with st.form("patient_form"):
        st.header("Patient Information")
        name = st.text_input("Full Name")
        age = st.number_input("Age", min_value=0, max_value=120)
        sex = st.selectbox("Gender", ["Male", "Female", "Other"])
        date = st.date_input("Exam Date", value=datetime.date.today())
        
        st.header("X-ray Upload")
        xray = st.file_uploader("Upload bitewing X-ray", type=["jpg", "jpeg", "png"])
        
        if st.form_submit_button("Submit Report"):
            if xray:
                st.session_state.patient_data = {
                    "name": name,
                    "age": age,
                    "sex": sex,
                    "date": date,
                    "xray": xray
                }
                st.session_state.page = "summary"
            else:
                st.warning("Please upload an X-ray image")

# -----------------------
# Page: Summary
# -----------------------
elif st.session_state.page == "summary" and st.session_state.authenticated:
    st.title("📋 Report Summary")
    
    # Display patient data
    data = st.session_state.patient_data
    st.subheader("Patient Details")
    st.write(f"**Name:** {data['name']}")
    st.write(f"**Age:** {data['age']}")
    st.write(f"**Gender:** {data['sex']}")
    st.write(f"**Exam Date:** {data['date'].strftime('%Y-%m-%d')}")
    
    st.subheader("X-ray Preview")
    st.image(data['xray'], use_column_width=True)
    
    # Save to Google Sheets
    if st.button("Save to Google Sheets"):
        gc = init_gsheets()
        if gc:
            try:
                sheet = gc.open("DentalReports").sheet1
                sheet.append_row([
                    data['name'],
                    data['age'],
                    data['sex'],
                    str(data['date']),
                    "X-ray uploaded"  # Store reference to image
                ])
                st.success("Data saved successfully!")
            except Exception as e:
                st.error(f"Save failed: {str(e)}")
    
    if st.button("New Report"):
        st.session_state.page = "input"
