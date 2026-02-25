import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

print("Inspecting 'tareas' columns...")
# Fetch one row to see keys, but this doesn't show null-valued columns if the library strips them.
# Better to assume missing if not seen in debug. 
# But let's try to infer from a "select all" on an empty or populated table.
# Actually, the best way with PostgREST/Supabase to see schema is hard without permissions to system tables.
# I will try to select 'duracion_minutos' specifically to see if it errors.

try:
    supabase.table("tareas").select("duracion_minutos").limit(1).execute()
    print("Column 'duracion_minutos' EXISTS.")
except Exception as e:
    print(f"Column 'duracion_minutos' MISSING: {e}")

try:
    supabase.table("tareas").select("predecesor_id").limit(1).execute()
    print("Column 'predecesor_id' EXISTS.")
except Exception as e:
    print(f"Column 'predecesor_id' MISSING: {e}")
