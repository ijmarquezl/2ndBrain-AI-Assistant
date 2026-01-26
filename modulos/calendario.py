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
            # FIX: Handle private_key newlines (often mangled in Streamlit Cloud Secrets)
            if "private_key" in creds_dict:
                pk = creds_dict["private_key"]
                
                # Aggressive Cleaning Strategy
                # 1. Remove existing headers/footers to isolate the payload
                body = pk.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
                
                # 2. Remove ALL whitespace (spaces, tabs, newlines, escaped newlines)
                body = body.replace(" ", "").replace("\n", "").replace("\\n", "").replace("\r", "")
                
                # 3. Check if body is empty
                if not body:
                    st.sidebar.error("❌ Key body is empty after cleaning!")
                
                # 3.5 Validate and Canonicalize Base64
                import base64
                import binascii
                try:
                    # Validate and clean by round-tripping
                    key_bytes = base64.b64decode(body) 
                    # Re-encode to ensure pristine base64 (no hidden chars, correct padding)
                    clean_body = base64.b64encode(key_bytes).decode('ascii')
                except binascii.Error as be:
                    st.sidebar.error(f"❌ Invalid Base64: {be}")
                    clean_body = body # Fallback to original if decode fails, though likely to fail later
                
                # 4. Reconstruct standard PEM format with 64-char folding
                def chunk_string(s, w):
                    return '\n'.join([s[i:i + w] for i in range(0, len(s), w)])

                fmt_body = chunk_string(clean_body, 64)
                # Ensure trailing newline after footer
                new_pk = f"-----BEGIN PRIVATE KEY-----\n{fmt_body}\n-----END PRIVATE KEY-----\n"
                
                creds_dict["private_key"] = new_pk
                # st.sidebar.success("🔑 Key processed and re-encoded.")
                
                # Debug end of key
                # st.sidebar.code(f"Key End: ...{clean_body[-20:]}")




            
            try:
                creds = service_account.Credentials.from_service_account_info(
                    creds_dict, scopes=SCOPES
                )
            except ValueError as ve:
                ve_str = str(ve)
                if "extra data" in ve_str or "ASN.1" in ve_str:
                    st.sidebar.error("❌ Key has TRAILING GARBAGE. Did you paste it twice?")
                raise ve

            # print("✅ Authenticated via st.secrets")
    except (FileNotFoundError, AttributeError, ValueError) as e:
        # It's normal to fail here locally if secrets.toml doesn't exist.
        # CAUTION: In Cloud, we WANT to see this error if it fails!
        st.sidebar.error(f"⚠️ Cloud Auth Error: {e}")
        # Debugging Helper: Show start of key to verify format (First 30 chars)
        if "google_credentials" in st.secrets:
             pk_debug = st.secrets["google_credentials"].get("private_key", "UNKNOWN")
             st.sidebar.code(f"Key Start: {pk_debug[:40]}...")
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
        st.sidebar.error("❌ No credentials loaded (Cloud or Local). Check secrets.toml.")
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
        # Priority: Env (Local) -> Secrets Top Level -> Secrets Nested -> Default
        if os.getenv("GOOGLE_CALENDAR_ID"):
             calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        else:
            # Try finding it in various places in st.secrets
            found = False
            try:
                # 1. Top Level
                if "GOOGLE_CALENDAR_ID" in st.secrets:
                    calendar_id = st.secrets["GOOGLE_CALENDAR_ID"]
                    found = True
                
                # 2. Nested in google_credentials (common mistake)
                elif "google_credentials" in st.secrets:
                    if "GOOGLE_CALENDAR_ID" in st.secrets["google_credentials"]:
                        calendar_id = st.secrets["google_credentials"]["GOOGLE_CALENDAR_ID"]
                        found = True
                    elif "calendar_id" in st.secrets["google_credentials"]:
                        calendar_id = st.secrets["google_credentials"]["calendar_id"]
                        found = True
                
                # DIAGNOSTIC: Show keys (safe)
                if not found:
                    st.sidebar.warning(f"🔍 Keys disponibles: {list(st.secrets.keys())}")
                    if "google_credentials" in st.secrets:
                         st.sidebar.warning(f"🔍 Keys en creds: {list(st.secrets['google_credentials'].keys())}")

            except (FileNotFoundError, AttributeError):
                pass 
        
        # VISIBLE DEBUG (Remove later)
        st.sidebar.warning(f"🕵️ ID: {calendar_id}")

        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId=calendar_id, 
            timeMin=now,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        st.sidebar.info(f"📅 Eventos: {len(events)}")
        
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
