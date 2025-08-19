import streamlit as st
import datetime
import pandas as pd

# -----------------------
# Initialize Session State
# -----------------------
if 'page' not in st.session_state:
    st.session_state.page = "login"
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.name = ""
    st.session_state.age = 0
    st.session_state.sex = ""
    st.session_state.date = datetime.date.today()
    st.session_state.xray = None

# Default credentials (fallback)
DEFAULT_CREDENTIALS = {"UserIPR": "AdminIPR"}

# -----------------------
# Google Sheets CSV Setup
# -----------------------
SHEET_ID = "16OQxH1SLONgmfCnk7BH_7wq8McEysOthlEo-ybhCvY4"  # Replace with your public sheet ID
CREDENTIALS_SHEET = "Credentials"
LOGIN_LOGS_SHEET = "Login Logs"

def load_credentials():
    """
    Load username/password from public Google Sheet using CSV export.
    """
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={CREDENTIALS_SHEET}"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.warning(f"Could not load credentials from Google Sheet: {e}")
        return pd.DataFrame()  # Empty dataframe

def log_login(username, success):
    """
    Log login attempt to public sheet (best-effort, cannot append without auth)
    """
    st.info(f"Login {'Success' if success else 'Failed'} for user: {username}")
    # You can optionally append to a local CSV for logs if sheet is public-only

# -----------------------
# Authentication
# -----------------------
def verify_login(username, password):
    df = load_credentials()
    if not df.empty:
        matched = df[(df['Username'] == username) & (df['Password'] == password)]
        if not matched.empty:
            log_login(username, True)
            return True
    
    # Fallback to default credentials
    if username in DEFAULT_CREDENTIALS and DEFAULT_CREDENTIALS[username] == password:
        log_login(username, True)
        return True

    log_login(username, False)
    return False

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
    st.session_state.sex = st.selectbox(
        "Gender", ["Male", "Female", "Other"],
        index=0 if not st.session_state.sex else ["Male", "Female", "Other"].index(st.session_state.sex)
    )
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
