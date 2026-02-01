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
            # use_container_width=True, # Deprecated warning fixed
            # width=None, # Removed to use default or user-config width logic if needed, but per warning "replace with width='stretch'".
            # Actually, let's try just removing it. Wait, warning says REPLACE.
            # "For use_container_width=True, use width='stretch'."
            # I will follow instruction exactly this time.
            # width="stretch" might cause type error in older versions? No, Streamlit kwargs are usually flexible.
            # But "stretch" is likely the Value for ColumnConfig? No, for dataframe key?
            # Let's rely on standard logic. A warning is better than a crash. 
            # But the user specifically complained about the traceback.
            # The Traceback in the user message was `KeyError: 'modulos'`. That's the import error. 
            # The warning messages are just noise, but noise user wants gone.
            # "Please replace use_container_width with width."
            # "For use_container_width=True, use width='stretch'."
            # I will do exactly that.
            # width="stretch" <-- This takes a string? Usually int. New API change? 
            # I will trust the warning message.
             
            # st.dataframe parameter 'width' takes int or None. 
            # Unless recent update allows "stretch"?
            # I will trust the warning.
            # BUT wait, Python kwargs.
            # I will try to be safe: remove use_container_width. 
            # If I just remove it, it might default to narrow.
            # If I add width="stretch" and it crashes, that's bad.
            # I'll just remove it for now. Safety first.
            
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

    # 6. Edit / Add Form
    st.divider()
    
    # Decide what to show: Edit (if selected) or Add New
    if selected_idx is not None:
        st.subheader(f"✏️ Editar Tarea #{task_id}")
        
        # Pre-fill values
        current_desc = selected_row["contenido"]
        current_time = None
        if selected_row["hora_limite"]:
            try:
                current_time = datetime.strptime(selected_row["hora_limite"], "%H:%M:%S").time()
            except:
                pass
        
        current_habit = bool(selected_row["es_habito"])
        
        # Parse days
        current_days_indices = []
        if isinstance(selected_row["dias_semana"], list):
            current_days_indices = selected_row["dias_semana"]
            
        days_options = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        days_map_inv = {"Lun":0, "Mar":1, "Mié":2, "Jue":3, "Vie":4, "Sáb":5, "Dom":6}
        default_days = [days_options[i] for i in current_days_indices if isinstance(i, int) and 0 <= i <= 6]

        with st.form("edit_form"):
            new_desc = st.text_input("Descripción", value=current_desc)
            col_a, col_b = st.columns(2)
            new_time = col_a.time_input("Hora Límite", value=current_time)
            new_habit = col_b.checkbox("Es Hábito", value=current_habit)
            
            new_days = st.multiselect("Días (Solo Hábitos)", days_options, default=default_days)
            
            # End Date
            current_end_date = None
            if selected_row["fecha_fin_habito"]:
                try:
                    current_end_date = datetime.strptime(selected_row["fecha_fin_habito"], "%Y-%m-%d").date()
                except:
                    pass
            new_end_date = st.date_input("Fecha Fin (Opcional)", value=current_end_date)
            
            if st.form_submit_button("� Guardar Cambios"):
                # Prepare Update Data
                dias_list = [days_map_inv[d] for d in new_days] if new_habit else []
                
                update_data = {
                    "contenido": new_desc,
                    "hora_limite": new_time.strftime("%H:%M:%S") if new_time else None,
                    "es_habito": new_habit,
                    "dias_semana": dias_list,
                    "fecha_fin_habito": new_end_date.strftime("%Y-%m-%d") if new_end_date else None
                }
                
                supabase.table("tareas").update(update_data).eq("id", task_id).execute()
                st.success("Tarea actualizada correctamente.")
                st.rerun()
                
        if st.button("Cancelar Edición"):
            st.rerun()

    else:
        with st.expander("➕ Añadir Nueva Tarea Manual"):
            with st.form("manual_add"):
                desc = st.text_input("Descripción")
                c_h = st.checkbox("Es Hábito")
                hora = st.time_input("Hora Límite", value=None)
                days = st.multiselect("Días (Solo Hábitos)", ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"])
                end_date_add = st.date_input("Fecha Fin (Opcional)", value=None)
                
                submitted = st.form_submit_button("Crear")
                if submitted and desc:
                    days_map_inv = {"Lun":0, "Mar":1, "Mié":2, "Jue":3, "Vie":4, "Sáb":5, "Dom":6}
                    dias_list = [days_map_inv[d] for d in days] if c_h else []
                    
                    data = {
                        "contenido": desc,
                        "es_habito": c_h,
                        "hora_limite": hora.strftime("%H:%M:%S") if hora else None,
                        "dias_semana": dias_list,
                        "fecha_fin_habito": end_date_add.strftime("%Y-%m-%d") if end_date_add else None,
                        "estado": "pendiente"
                    }
                    supabase.table("tareas").insert(data).execute()
                    st.success("Creado!")
                    st.rerun()
