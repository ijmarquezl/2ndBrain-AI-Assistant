import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load Env
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CREDENTIALS_FILE = 'google_credentials.json'

def debug_calendar_access():
    print("🕵️‍♂️ Starting Calendar Debugger...")
    
    # 1. Check Credentials File
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: {CREDENTIALS_FILE} not found.")
        return

    # 2. Authenticate
    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=creds)
        print("✅ Service Account Authenticated.")
    except Exception as e:
        print(f"❌ Auth Failed: {e}")
        return

    # 3. Check Target Calendar ID
    target_id = os.getenv("GOOGLE_CALENDAR_ID")
    if not target_id:
        print("❌ GOOGLE_CALENDAR_ID is missing in .env")
        return
    print(f"🎯 Target Calendar ID: '{target_id}'")

    # 4. Try to List Events
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        print(f"🕒 Querying events from: {now}")
        
        events_result = service.events().list(
            calendarId=target_id, 
            timeMin=now,
            maxResults=10, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("⚠️ No upcoming events found (Authentication worked, but list is empty).")
        else:
            print(f"✅ Found {len(events)} events:")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"   - {start}: {event.get('summary', 'No Title')}")

    except Exception as e:
        print(f"❌ API Request Failed!")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n💡 Troubleshooting:")
        print("   - 404 Not Found: The Calendar ID is wrong OR the calendar is not shared with the service account.")
        print(f"   - 403 Forbidden: Service Account email wasn't added to the calendar sharing settings.")
        
        # Print Service Account Email for verification
        try:
             # Hacky way to get email from private key file content if needed, 
             # but usually it's in the error details or we assume the user knows it.
             pass
        except: 
             pass

if __name__ == "__main__":
    debug_calendar_access()
