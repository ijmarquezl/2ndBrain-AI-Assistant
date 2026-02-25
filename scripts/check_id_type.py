import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

print("Fetching one task to inspect ID type...")
try:
    response = supabase.table("tareas").select("id").limit(1).execute()
    if response.data:
        task_id = response.data[0]['id']
        print(f"ID Value: {task_id}")
        print(f"ID Type (Python): {type(task_id)}")
    else:
        print("Table 'tareas' is empty. Cannot determine type from data.")
except Exception as e:
    print(f"Error: {e}")
