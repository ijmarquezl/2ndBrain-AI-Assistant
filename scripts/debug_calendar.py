import os
import streamlit as st
from modulos.calendario import get_calendar_service

def debug_calendars():
    print("🔍 Inspecting Accessible Calendars...")
    service = get_calendar_service()
    if not service:
        print("❌ Could not Authenticate.")
        return

    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            print(f"------------")
            print(f"ID: {calendar_list_entry['id']}")
            print(f"Summary: {calendar_list_entry.get('summary')}")
            print(f"Primary: {calendar_list_entry.get('primary', False)}")
            print(f"AccessRole: {calendar_list_entry.get('accessRole')}")
        
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break

if __name__ == "__main__":
    debug_calendars()
