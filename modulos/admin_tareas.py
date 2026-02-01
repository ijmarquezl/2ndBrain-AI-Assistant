import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from datetime import datetime

def render_admin_tareas():
    st.header("📋 Gestor de Tareas y Recordatorios")
    
    # 1. Initialize DB
    url: str = os.getenv("SUPABASE_URL")
    key: str = os.getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("Faltan credenciales de Supabase en .env")
        return

    supabase: Client = create_client(url, key)
    
    # 2. Fetch Data
    try:
        # Fetch all tasks order by ID desc
        response = supabase.table("tareas").select("*").order("id", desc=True).execute()
        tasks = response.data
    except Exception as e:
        st.error(f"Error al conectar con DB: {e}")
        return

    if not tasks:
        st.info("No hay tareas registradas.")
        return

    # 3. Process Data for Display
    df = pd.DataFrame(tasks)
    
    # Ensure columns exist (handle old schema rows)
    expected_cols = ["id", "contenido", "estado", "es_habito", "hora_limite", "fecha_limite", "dias_semana", "fecha_fin_habito"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    # Filter Sidebar
    st.sidebar.subheader("Filtros")
    # DEFAULT EMPTY to show all by default
    filtro_estado = st.sidebar.multiselect("Estado", df["estado"].unique(), default=[]) 
    mostrar_habitos = st.sidebar.checkbox("Mostrar Solo Hábitos", value=False)
    
    # Apply Filters
    if filtro_estado:
        df = df[df["estado"].isin(filtro_estado)]
    if mostrar_habitos:
        df = df[df["es_habito"] == True]

    # Show Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tareas", len(tasks))
    col2.metric("Pendientes", len(df[df["estado"] == "pendiente"]))
    col3.metric("Hábitos Activos", len(df[df["es_habito"] == True]))

    st.divider()

    # 4. Interactive Data Editor
    # We use data_editor to allow some edits if possible, or just display nicely
    
    # Enhance display columns
    display_df = df.copy()
    
    # Format days for readability
    def format_days(d):
        if not d: return "-"
        days_map = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
        try:
             # If it's a list
             if isinstance(d, list):
                 return ", ".join([days_map.get(x, str(x)) for x in d])
             return str(d)
        except:
             return str(d)

    display_df["dias_semana"] = display_df["dias_semana"].apply(format_days)
    
    # Columns to show
    cols_show = ["id", "contenido", "estado", "es_habito", "hora_limite", "dias_semana", "fecha_limite", "fecha_fin_habito"]
    
    # Safe rendering for older streamlit versions
    selected_idx = None
    try:
        event = st.dataframe(
            display_df[cols_show],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            
    except TypeError:
        # Fallback for older Streamlit versions without on_select
        st.warning("⚠️ Tu versión de Streamlit es antigua. Selección interactiva desactivada.")
        st.dataframe(
            display_df[cols_show],
            use_container_width=True,
            hide_index=True
        )
        
    # 5. Actions on Selection
    if selected_idx is not None:
        selected_row = display_df.iloc[selected_idx]
        task_id = int(selected_row["id"])
        
        st.subheader(f"Acciones para Tarea #{task_id}")
        st.text(f"Contenido: {selected_row['contenido']}")
        
        c1, c2, c3 = st.columns(3)
        
        if c1.button("✅ Completar"):
            supabase.table("tareas").update({"estado": "completado"}).eq("id", task_id).execute()
            st.success("Tarea marcada como completada!")
            st.rerun()
            
        if c2.button("🗑️ Eliminar"):
            supabase.table("tareas").delete().eq("id", task_id).execute()
            st.warning("Tarea eliminada.")
            st.rerun()

        if c3.button("🔄 Reactivar"):
             supabase.table("tareas").update({"estado": "pendiente"}).eq("id", task_id).execute()
             st.success("Tarea reactivada!")
             st.rerun()

    # 6. Manual Debugging / Add (Optional)
    with st.expander("🛠️ Debug / Añadir Manual"):
        with st.form("manual_add"):
            desc = st.text_input("Descripción")
            c_h = st.checkbox("Es Hábito")
            hora = st.time_input("Hora Límite", value=None)
            days = st.multiselect("Días (Solo Hábitos)", ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"])
            
            submitted = st.form_submit_button("Crear")
            if submitted and desc:
                days_map_inv = {"Lun":0, "Mar":1, "Mié":2, "Jue":3, "Vie":4, "Sáb":5, "Dom":6}
                dias_list = [days_map_inv[d] for d in days] if c_h else []
                
                data = {
                    "contenido": desc,
                    "es_habito": c_h,
                    "hora_limite": hora.strftime("%H:%M:%S") if hora else None,
                    "dias_semana": dias_list,
                    "estado": "pendiente"
                }
                supabase.table("tareas").insert(data).execute()
                st.success("Creado!")
                st.rerun()
