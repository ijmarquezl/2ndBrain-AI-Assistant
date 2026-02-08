import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

sql = """
-- Add duration and dependency columns for Gantt Chart support
DO $$ 
BEGIN 
    -- 1. Duration (Default 60 mins)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'tareas' AND column_name = 'duracion_minutos') THEN
        ALTER TABLE tareas ADD COLUMN duracion_minutos INTEGER DEFAULT 60;
    END IF;

    -- 2. Dependency (Predecessor)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'tareas' AND column_name = 'predecesor_id') THEN
        ALTER TABLE tareas ADD COLUMN predecesor_id UUID REFERENCES tareas(id) ON DELETE SET NULL;
    END IF;

    -- 3. Start Date (Explicit override, otherwise calculated)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'tareas' AND column_name = 'fecha_inicio') THEN
        ALTER TABLE tareas ADD COLUMN fecha_inicio TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;
"""

print("⚠️ Automatic migration via Client is NOT supported for DDLStatements.")
print("Please run the following SQL in your Supabase SQL Editor:")
print("-" * 50)
print(sql)
print("-" * 50)
