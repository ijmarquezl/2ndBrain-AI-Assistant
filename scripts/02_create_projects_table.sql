-- 1. Create Projects Table
create table if not exists proyectos (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  nombre text not null,
  descripcion text,
  estado text default 'activo' check (estado in ('activo', 'completado', 'archivado'))
);

-- 2. Enable RLS (Row Level Security) - Optional best practice, but keep open for now if policies aren't set
alter table proyectos enable row level security;

-- 3. Create Policy (Allow all access for now, similar to existing setup usually)
-- IF you have authentication enabled, change this to auth.uid() = user_id
create policy "Enable all access for now" on proyectos for all using (true);

-- 4. Add Foreign Key to Tareas
alter table tareas 
add column if not exists proyecto_id uuid references proyectos(id) on delete set null;

-- 5. Create Index for performance
create index if not exists idx_tareas_proyecto_id on tareas(proyecto_id);
