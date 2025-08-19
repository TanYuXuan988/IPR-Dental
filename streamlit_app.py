import streamlit as st
from PIL import Image
import datetime
import gspread
from gspread_pandas import Spread, Client
import pandas as pd

# -----------------------
# Configuration
# -----------------------
SHEET_ID = "16OQxH1SLONgmfCnk7BH_7wq8McEysOthlEo-ybhCvY4"  # Replace with your Google Sheet ID
API_KEY = "AIzaSyCVxzdF0Bm0seKbB6KKdOuBC93aoNafUNo"    # Replace with your Google API key
DEFAULT_USERNAME = "UserIPR"
DEFAULT_PASSWORD = "AdminIPR"

# Initialize Google Sheets connection
def init_gsheets():
    try:
        config = {'apiKey': API_KEY}
        spreadsheet = Spread(SHEET_ID, config=config)
        return spreadsheet
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        return None

spreadsheet = init_gsheets()

# -----------------------
# Helper Functions
# -----------------------
def get_credentials():
    if not spreadsheet:
        return DEFAULT_USERNAME, DEFAULT_PASSWORD
    
    try:
        df = spreadsheet.sheet_to_df(sheet="Credentials")
        if not df.empty:
            return df.iloc[0]['username'], df.iloc[0]['password']
        return DEFAULT_USERNAME, DEFAULT_PASSWORD
    except:
        return DEFAULT_USERNAME, DEFAULT_PASSWORD

def update_credentials(new_password):
    if not spreadsheet:
        st.error("Not connected to Google Sheets")
        return False
    
    try:
        cred_data = pd.DataFrame({
            'username': [DEFAULT_USERNAME],
            'password': [new_password]
        })
        spreadsheet.df_to_sheet(cred_data, sheet="Credentials", index=False, replace=True)
        return True
    except Exception as e:
        st.error(f"Failed to update credentials: {e}")
        return False

def log_login(username, success):
    if not spreadsheet:
        return
    
    try:
        # Get existing logs
        try:
            logs_df = spreadsheet.sheet_to_df(sheet="LoginLogs")
        except:
            logs_df = pd.DataFrame(columns=['Timestamp', 'Username', 'Status'])
        
        # Add new log
        new_log = pd.DataFrame([{
            'Timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Username': username,
            'Status': "Success" if success else "Failed"
        }])
        
        updated_logs = pd.concat([logs_df, new_log], ignore_index=True)
        spreadsheet.df_to_sheet(updated_logs, sheet="LoginLogs", index=False, replace=True)
    except Exception as e:
        st.error(f"Failed to log login: {e}")

def login(user, pwd):
    stored_user, stored_pwd = get_credentials()
    if user == stored_user and pwd == stored_pwd:
        st.session_state.authenticated = True
        st.session_state.page = "input"
        st.session_state.username = user
        log_login(user, True)
        st.success("Login successful ✅")
    else:
        log_login(user, False)
        st.error("Invalid username or password ❌")

def logout():
    log_login(st.session_state.username, False)
    st.session_state.authenticated = False
    st.session_state.page = "login"

def change_password(old_pwd, new_pwd):
    stored_user, stored_pwd = get_credentials()
    if old_pwd == stored_pwd:
        if update_credentials(new_pwd):
            st.success("Password changed successfully ✅")
        else:
            st.error("Failed to update password in storage ❌")
    else:
        st.error("Old password is incorrect ❌")

def go_to_next():
    st.session_state.page = "summary"

# -----------------------
# Initialize session state
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
        login(user, pwd)

# -----------------------
# Page: Patient Input
# -----------------------
elif st.session_state.page == "input" and st.session_state.get("authenticated", False):
    st.title("🦷 Dental X-ray Report - Step 1")

    st.sidebar.title("⚙️ Settings")
    if st.sidebar.button("Logout"):
        logout()

    with st.sidebar.expander("Change Password"):
        old_pwd = st.text_input("Old Password", type="password")
        new_pwd = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            change_password(old_pwd, new_pwd)

    st.header("👤 Patient Information")
    name = st.text_input("Name", key="name")
    age = st.number_input("Age", min_value=0, max_value=120, key="age")
    sex = st.selectbox("Gender", ["Male", "Female", "Other"], key="sex")
    date = st.date_input("Examination Date", key="date", value=datetime.date.today())

    st.header("📸 Upload Dental X-ray")
    uploaded_file = st.file_uploader("Upload a bitewing X-ray", type=["jpg", "jpeg", "png"], key="xray")

    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        st.markdown("---")
        st.button("Next ➡️", on_click=go_to_next)
    else:
        st.info("Please upload an X-ray image to continue.")

# -----------------------
# Page: Summary
# -----------------------
elif st.session_state.page == "summary" and st.session_state.get("authenticated", False):
    st.title("📋 Dental X-ray Report Summary")

    st.sidebar.title("⚙️ Settings")
    if st.sidebar.button("Logout"):
        logout()

    with st.sidebar.expander("Change Password"):
        old_pwd = st.text_input("Old Password", type="password")
        new_pwd = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            change_password(old_pwd, new_pwd)

    st.subheader("Patient Details")
    st.write(f"**Name:** {st.session_state.name}")
    st.write(f"**Age:** {st.session_state.age}")
    st.write(f"**Gender:** {st.session_state.sex}")
    st.write(f"**Examination Date:** {st.session_state.date.strftime('%B %d, %Y')}")

    st.subheader("Uploaded X-ray Image")
    st.image(st.session_state.xray, use_container_width=True)

    st.success("Patient data loaded successfully. Machine learning analysis will be available soon.")
    st.button("⬅️ Back", on_click=lambda: st.session_state.update(page="input"))
