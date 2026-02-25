import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

try:
    print("Checking 'proyectos' table...")
    response = supabase.table("proyectos").select("count", count="exact").execute()
    print(f"Table 'proyectos' exists. Row count: {response.count}")
except Exception as e:
    print(f"Error accessing 'proyectos': {e}")
    
try:
    print("Checking 'tareas.proyecto_id' column...")
    # Try to select the column
    response = supabase.table("tareas").select("proyecto_id").limit(1).execute()
    print("Column 'proyecto_id' in 'tareas' exists.")
except Exception as e:
    print(f"Error accessing 'tareas.proyecto_id': {e}")
