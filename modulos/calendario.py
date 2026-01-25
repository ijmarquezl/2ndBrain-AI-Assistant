import os
import datetime
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
LOCAL_CREDENTIALS_PATH = "google_credentials.json"

def get_calendar_service():
    """
    Authenticates with Google Calendar API using Service Account.
    Tries Streamlit Secrets first (Cloud), then local JSON file (Local).
    """
    creds = None
    
    # 1. Try Streamlit Secrets (Cloud)
    # Expected format: st.secrets["google_credentials"] as a dictionary
    try:
        if "google_credentials" in st.secrets:
            creds_dict = dict(st.secrets["google_credentials"])
            
            # FIX: Handle private_key newlines (often mangled in Streamlit Cloud Secrets)
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
            creds = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=SCOPES
            )
            # print("✅ Authenticated via st.secrets")
    except (FileNotFoundError, AttributeError, ValueError) as e:
        # st.error(f"Secrets Error: {e}") # debug
        pass

    # 2. Try Local File (Fall back)
    if not creds and os.path.exists(LOCAL_CREDENTIALS_PATH):
        try:
            creds = service_account.Credentials.from_service_account_file(
                LOCAL_CREDENTIALS_PATH, scopes=SCOPES
            )
            # print(f"✅ Authenticated via {LOCAL_CREDENTIALS_PATH}")
        except Exception as e:
            st.error(f"Error loading local credentials: {e}")

    if not creds:
        # Return None so the app handles it gracefully (e.g. shows "Not configured")
        return None

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Failed to build Calendar service: {e}")
        return None

def get_upcoming_events(max_results=5):
    """
    Returns a list of upcoming events from the primary calendar.
    """
    service = get_calendar_service()
    if not service:
        return []

    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
    except Exception as e:
        # print(f"Calendar API Error: {e}")
        return []
