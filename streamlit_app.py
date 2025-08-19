import streamlit as st
import datetime
import gspread
import pandas as pd

# -----------------------
# Configuration
# -----------------------
st.set_page_config(page_title="Dental Report", layout="centered")

# Default credentials (will work without Google Sheets)
DEFAULT_CREDENTIALS = {
    "UserIPR": "AdminIPR"  # username: password
}

# -----------------------
# Google Sheets Setup
# -----------------------
def init_gsheets():
    try:
        # Method 1: Public access (no auth needed)
        gc = gspread.service_account(filename='.streamlit/secrets.json')
        return gc
    except:
        try:
            # Method 2: API key fallback
            gc = gspread.Client(auth={'api_key': st.secrets["gsheets_api_key"]})
            return gc
        except Exception as e:
            st.error("Couldn't connect to Google Sheets")
            return None

# -----------------------
# Authentication
# -----------------------
def verify_login(username, password):
    # Try Google Sheets first
    gc = init_gsheets()
    if gc:
        try:
            sheet = gc.open("IPR Login Logsheet").worksheet("Credentials")
            records = sheet.get_all_records()
            for record in records:
                if record['Username'] == username and record['Password'] == password:
                    log_login(username, True)
                    return True
        except:
            pass
    
    # Fallback to default credentials
    if username in DEFAULT_CREDENTIALS and DEFAULT_CREDENTIALS[username] == password:
        log_login(username, True)
        return True
    
    log_login(username, False)
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
        except:
            pass

# -----------------------
# Pages (your existing UI)
# -----------------------
if st.session_state.page == "login":
    # [Your existing login page code]
    pass
elif st.session_state.page == "input":
    # [Your existing input page code]
    pass
elif st.session_state.page == "summary":
    # [Your existing summary page code]
    pass
