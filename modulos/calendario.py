import os
import datetime
import streamlit as st
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load env immediately (for local dev)
load_dotenv()

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
        # It's normal to fail here locally if secrets.toml doesn't exist.
        # We rely on .env fallback next.
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
        # Service Accounts have their own 'primary' calendar (empty).
        # We need to query the USER'S shared calendar ID (usually their email).
        calendar_id = 'primary' # Default fallback
        
        # Check Secrets/Env for specific ID
        # Check Secrets/Env for specific ID
        # Priority: Env (Local) -> Secrets (Cloud)
        if os.getenv("GOOGLE_CALENDAR_ID"):
             calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        else:
            try:
                if "GOOGLE_CALENDAR_ID" in st.secrets:
                    calendar_id = st.secrets["GOOGLE_CALENDAR_ID"]
            except (FileNotFoundError, AttributeError):
                pass # Local dev without secrets.toml
        
        # VISIBLE DEBUG (Remove later)
        # st.sidebar.warning(f"🕵️ ID: {calendar_id}")

        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId=calendar_id, 
            timeMin=now,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        # st.sidebar.info(f"📅 Eventos: {len(events)}")
        
        print(f"DEBUG: Using Calendar ID: {calendar_id}")
        print(f"DEBUG: Found {len(events)} events")
        return events
    except Exception as e:
        print(f"❌ Calendar API Error in App: {e}")
        return []

def add_event_to_calendar(summary, start_datetime_iso, duration_minutes=60):
    """
    Creates an event in the user's calendar.
    start_datetime_iso: "YYYY-MM-DDTHH:MM:SS" (or similar ISO format)
    """
    service = get_calendar_service()
    if not service:
        return False

    try:
        # Determine Calendar ID
        calendar_id = 'primary'
        if os.getenv("GOOGLE_CALENDAR_ID"):
             calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        else:
            try:
                if "GOOGLE_CALENDAR_ID" in st.secrets:
                    calendar_id = st.secrets["GOOGLE_CALENDAR_ID"]
            except: pass

        # Parse start time
        # Ensure we have a valid ISO string. If it comes from DB, it might include offset or not.
        from dateparser import parse
        dt_start = parse(start_datetime_iso)
        if not dt_start:
            print("❌ Invalid Date format")
            return False
            
        dt_end = dt_start + datetime.timedelta(minutes=duration_minutes)

        event_body = {
            'summary': summary,
            'start': {
                'dateTime': dt_start.isoformat(),
                'timeZone': 'UTC', # Ideally should match user's timezone, simplified for now
            },
            'end': {
                'dateTime': dt_end.isoformat(),
                'timeZone': 'UTC',
            },
        }

        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        print(f"✅ Event created: {event.get('htmlLink')}")
        return True

    except Exception as e:
        print(f"❌ Failed to create event: {e}")
        return False
