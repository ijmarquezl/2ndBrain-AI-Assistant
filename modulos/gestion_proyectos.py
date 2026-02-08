import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from supabase import create_client
import os
from datetime import datetime, timedelta

def calculate_cpm(tasks_df):
    """
    Calculates Critical Path Method (CPM) for a set of tasks.
    Returns the dataframe with 'start', 'finish', 'slack', and 'is_critical' columns.
    """
    if tasks_df.empty:
        return tasks_df

    # 1. Initialize
    tasks = tasks_df.copy()
    tasks['id'] = tasks['id'].astype(str)
    tasks['predecesor_id'] = tasks['predecesor_id'].astype(str).replace('None', None).replace('nan', None)
    
    # Map ID to details for quick lookup
    task_map = {row['id']: {'duration': row.get('duracion_minutos', 60), 'predecessors': [], 'successors': [], 'es': 0, 'ef': 0, 'ls': float('inf'), 'lf': float('inf')} for index, row in tasks.iterrows()}

    # Buil Graph
    for index, row in tasks.iterrows():
        pid = row['predecesor_id']
        tid = row['id']
        if pid and pid in task_map:
            task_map[tid]['predecessors'].append(pid)
            task_map[pid]['successors'].append(tid)

    # 2. Forward Pass (Calculate Early Start & Early Finish)
    # Topological sort isn't strictly needed if we iterate until convergence, but simple BFS/level approach works for DAGs.
    # We'll use a simple iterative approach since usually project graphs are small.
    
    changed = True
    while changed:
        changed = False
        for tid in task_map:
            node = task_map[tid]
            # ES = max(EF of predecessors)
            if not node['predecessors']:
                es = 0
            else:
                es = max([task_map[p]['ef'] for p in node['predecessors']], default=0)
            
            ef = es + node['duration']
            
            if node['es'] != es or node['ef'] != ef:
                node['es'] = es
                node['ef'] = ef
                changed = True

    # Project Duration
    project_duration = max([node['ef'] for node in task_map.values()], default=0)

    # 3. Backward Pass (Calculate Late Start & Late Finish)
    # LS = LF - Duration
    # LF = min(LS of successors)
    
    # Initialize LF to Project Duration for end nodes
    for tid in task_map:
        if not task_map[tid]['successors']:
            task_map[tid]['lf'] = project_duration
            task_map[tid]['ls'] = project_duration - task_map[tid]['duration']

    changed = True
    while changed:
        changed = False
        for tid in task_map:
            node = task_map[tid]
            # LF = min(LS of successors)
            if node['successors']:
                lf = min([task_map[s]['ls'] for s in node['successors']], default=project_duration)
            else:
                 lf = project_duration # Should already be set, but re-enforce
            
            ls = lf - node['duration']

            if node['lf'] != lf or node['ls'] != ls:
                node['lf'] = lf
                node['ls'] = ls
                changed = True
                
    # 4. Calculate Slack and Critical Path
    results = []
    base_start_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    
    for index, row in tasks.iterrows():
        tid = row['id']
        node = task_map[tid]
        slack = node['ls'] - node['es']
        is_critical = (slack == 0)
        
        # Convert offset minutes to Real Datetimes (Business Hours simplified: just add minutes linearly for now)
        # TODO: Skip nights/weekends in future
        start_dt = base_start_date + timedelta(minutes=node['es'])
        end_dt = base_start_date + timedelta(minutes=node['ef'])
        
        results.append({
            'id': tid,
            'Start': start_dt,
            'Finish': end_dt,
            'Slack': slack,
            'Critical': is_critical,
            'Task': row['contenido'] # specific key for Plotly
        })
        
    return pd.DataFrame(results)

def render_gestion_proyectos():
    st.header("🏗️ Gestión de Proyectos y Gantt")
    
    # 1. Connect DB
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("Credenciales de Supabase faltantes.")
        return
    supabase = create_client(url, key)

    # 2. Select Project
    try:
        proyectos = supabase.table("proyectos").select("*").order("created_at", desc=True).execute().data
    except Exception as e:
        st.error(f"Error cargando proyectos: {e}")
        return

    if not proyectos:
        st.info("No tienes proyectos creados aún. Pídele al Coach Socrático que cree uno.")
        return
    
    proj_options = {p['id']: p['nombre'] for p in proyectos}
    selected_proj_id = st.selectbox("Selecciona un Proyecto", list(proj_options.keys()), format_func=lambda x: proj_options[x])
    
    # 3. Fetch Tasks for Project
    if selected_proj_id:
        try:
            # Need columns for CPM: id, contenido, duracion_minutos, predecesor_id
            # If columns don't exist yet (migration pending), this might fail. We handle gracefully.
            tasks_data = supabase.table("tareas").select("*").eq("proyecto_id", selected_proj_id).execute().data
            
            if not tasks_data:
                st.warning("Este proyecto no tiene tareas.")
                return
                
            df_tasks = pd.DataFrame(tasks_data)
            
            # --- Check Migration Schema ---
            missing_cols = []
            if "duracion_minutos" not in df_tasks.columns: missing_cols.append("duracion_minutos")
            if "predecesor_id" not in df_tasks.columns: missing_cols.append("predecesor_id")
            
            if missing_cols:
                st.error(f"⚠️ Faltan columnas en la base de datos para Gantt: {', '.join(missing_cols)}")
                st.info("Por favor ejecuta la migración SQL (`scripts/manual_migration_gantt.py` instructions).")
                # Show basic table meanwhile
                st.dataframe(df_tasks[["contenido", "estado"]])
                return

            # --- EDITOR ---
            st.subheader("📋 Definición de Tareas (Edita duración y dependencias)")
            
            # Prepare Editor DF
            editor_df = df_tasks[["id", "contenido", "duracion_minutos", "predecesor_id", "estado"]].copy()
            editor_df["duracion_minutos"] = editor_df["duracion_minutos"].fillna(60) # Default 1h
            
            # Helper for predecessor selection (shows ID but we want names usually, but ID for unique ref)
            # Simplification: User enters ID manually or we provide simple dropdown in future? 
            # DataEditor is limited for foreign key dropdowns. We'll use text input for UUID for now or just integer index if mapped.
            # Let's keep it checking 'predecesor_id' as string.
            
            updated_df = st.data_editor(editor_df, key="gantt_editor", num_rows="dynamic")
            
            if st.button("💾 Guardar Cambios"):
                # Save updates to DB
                # This could be optimized to batch updates, but simple loop for now
                for index, row in updated_df.iterrows():
                    # Sanitize
                    dur = int(row['duracion_minutos']) if row['duracion_minutos'] else 60
                    pid = row['predecesor_id'] 
                    if pd.isna(pid) or pid == "None" or pid == "": pid = None
                    
                    supabase.table("tareas").update({
                        "duracion_minutos": dur,
                        "predecesor_id": pid
                    }).eq("id", row['id']).execute()
                
                st.success("Guardado!")
                st.rerun()

            # --- GANTT & CPM ---
            st.divider()
            st.subheader("📊 Diagrama de Gantt & Ruta Crítica")
            
            cpm_df = calculate_cpm(updated_df)
            
            if not cpm_df.empty:
                # Color map based on Critical
                colors = {True: 'rgb(220, 50, 50)', False: 'rgb(50, 150, 250)'}
                
                fig = px.timeline(
                    cpm_df, 
                    x_start="Start", 
                    x_end="Finish", 
                    y="Task",
                    color="Critical",
                    color_discrete_map=colors,
                    title="Cronograma del Proyecto (Rojo = Ruta Crítica)",
                    hover_data=["Slack"]
                )
                
                # Reverse y axis to show first tasks on top
                fig.update_yaxes(autorange="reversed")
                
                # Add arrows? Hard in plotly timeline directly, usually requires annotations.
                # For MVP, just bars.
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Stats
                project_end = cpm_df['Finish'].max()
                total_duration_hours = (project_end - cpm_df['Start'].min()).total_seconds() / 3600
                st.metric("Duración Total Estimada", f"{total_duration_hours:.1f} Horas")
                st.caption(f"Fecha fin estimada (desde ahora): {project_end.strftime('%Y-%m-%d %H:%M')}")

        except Exception as e:
            st.error(f"Error procesando Gantt: {e}")
