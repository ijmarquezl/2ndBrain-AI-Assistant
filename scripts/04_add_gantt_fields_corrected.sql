-- CORRECTED: Add duration and dependency columns for Gantt Chart support
-- Using BIGINT for predecesor_id to match tareas.id type

-- 1. Duration (Default 60 mins)
ALTER TABLE tareas 
ADD COLUMN IF NOT EXISTS duracion_minutos INTEGER DEFAULT 60;

-- 2. Dependency (Predecessor) - CHANGED TO BIGINT
ALTER TABLE tareas 
ADD COLUMN IF NOT EXISTS predecesor_id BIGINT REFERENCES tareas(id) ON DELETE SET NULL;

-- 3. Start Date (Explicit override, otherwise calculated)
ALTER TABLE tareas 
ADD COLUMN IF NOT EXISTS fecha_inicio TIMESTAMP WITH TIME ZONE;

-- 4. Create Index for self-joins
CREATE INDEX IF NOT EXISTS idx_tareas_predecesor ON tareas(predecesor_id);
