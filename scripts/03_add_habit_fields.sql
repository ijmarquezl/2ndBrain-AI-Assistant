-- Add columns for robust habit tracking
ALTER TABLE tareas 
ADD COLUMN IF NOT EXISTS dias_semana jsonb DEFAULT '[]'::jsonb, -- e.g. [0, 6] for Mon, Sun
ADD COLUMN IF NOT EXISTS fecha_fin_habito date; -- Optional end date
