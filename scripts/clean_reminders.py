import os
import sys

# Add root project dir to path to import modules properly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client, Client
from modulos.calendario import get_calendar_service
import googleapiclient.errors

# Load Env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("❌ Missing Supabase environment variables. Check .env")
    exit(1)

# Init Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_database():
    print("🗑️  Cleaning 'tareas' table in Supabase...")
    try:
        # Since we want to delete ALL tasks:
        # We fetch all tasks first to know how many we delete
        response = supabase.table("tareas").select("id").execute()
        count = len(response.data) if response.data else 0
        
        if count == 0:
            print("✅ No tasks found in the database.")
            return

        # Supabase API usually requires a filter to run delete. 
        # We can delete all items where id is not null.
        res_del = supabase.table("tareas").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        # Verify
        print(f"✅ Executed delete operation for tasks. (Total IDs queried: {count})")
        
    except Exception as e:
        print(f"❌ Error deleting tasks from database: {e}")

def clean_calendar():
    print("\n🗑️  Cleaning upcoming events from Google Calendar...")
    service = get_calendar_service()
    if not service:
        print("❌ Could not get Google Calendar service. Is the credential set up correctly?")
        return

    try:
        # Determine Calendar ID
        calendar_id = 'primary'
        if os.getenv("GOOGLE_CALENDAR_ID"):
             calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
             
        # Use existing logic from get_upcoming_events but ask for more events to purge
        import datetime
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id, 
            timeMin=now,
            maxResults=2500, # Large number to clear batch
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print("✅ No upcoming events found in Calendar.")
            return
            
        deleted_count = 0
        for event in events:
            try:
                service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
                deleted_count += 1
                print(f"  Deleted event: {event.get('summary', 'Untitled')}")
            except googleapiclient.errors.HttpError as e:
                print(f"  ⚠️ Error deleting event {event.get('summary', 'Untitled')}: {e}")
                
        print(f"✅ Deleted {deleted_count} events from Google Calendar.")

    except Exception as e:
        print(f"❌ Error cleaning Google Calendar: {e}")

if __name__ == "__main__":
    print("🚀 Starting Reminders and Events Cleanup...\n")
    clean_database()
    clean_calendar()
    print("\n🎉 Cleanup Complete!")
