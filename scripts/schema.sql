-- Habilitar la extensión pgvector para trabajar con embeddings
create extension if not exists vector;

-- Tabla para almacenar tareas (Resultados del Coach Socrático)
create table if not exists tareas (
  id bigint primary key generated always as identity,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  contenido text not null,
  motivacion text, -- "El Porqué" raíz identificado
  estado text default 'pendiente', -- pendiente, completada, descartada
  tipo_tarea text -- creativa, administrativa, etc.
);

-- Tabla para Logs Emocionales (Resultados del Monitor Emocional)
create table if not exists logs_emocionales (
  id bigint primary key generated always as identity,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  input_usuario text not null,
  analisis_detectado text,
  reencuadre_sugerido text -- El consejo estoico/aikido dado
);

-- Tabla para Base de Conocimiento (RAG)
create table if not exists documentos (
  id bigint primary key generated always as identity,
  contenido text,
  metadata jsonb,
  embedding vector(768) -- Dimensión para modelos Gemini/Gecko
);

-- Función básica para búsqueda por similitud
create or replace function match_documents (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  contenido text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    documentos.id,
    documentos.contenido,
    documentos.metadata,
    1 - (documentos.embedding <=> query_embedding) as similarity
  from documentos
  where 1 - (documentos.embedding <=> query_embedding) > match_threshold
  order by documentos.embedding <=> query_embedding
  limit match_count;
end;
$$;
