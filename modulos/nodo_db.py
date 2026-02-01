import os
import dateparser
from supabase import create_client, Client
from core.grafo import EstadoGeneral
from langchain_core.messages import AIMessage

# Inicializar Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def nodo_db_saver(state: EstadoGeneral) -> dict:
    """
    Guarda la tarea aprobada en la base de datos Supabase.
    """
    # Extraer el mensaje del Asistente (Coach)
    mensajes = state["messages"]
    last_ai_msg = mensajes[-1] # Assuming the last message is from the AI because we just came from Coach Node
    
    # --- 1. TOOL CALL HANDLER (NUEVOS PROYECTOS) ---
    if hasattr(last_ai_msg, 'tool_calls') and last_ai_msg.tool_calls:
        tool_call = last_ai_msg.tool_calls[0]
        if tool_call["name"] == "PlanProyecto":
            args = tool_call["args"]
            nombre_proy = args.get("nombre_proyecto")
            desc_proy = args.get("descripcion")
            tareas_lista = args.get("tareas", [])
            
            print(f"🚀 Creando Proyecto: {nombre_proy}")
            
            try:
                # A. Crear Proyecto
                res_proy = supabase.table("proyectos").insert({
                    "nombre": nombre_proy,
                    "descripcion": desc_proy,
                    "estado": "activo"
                }).execute()
                
                if not res_proy.data:
                    raise Exception("No se pudo crear el proyecto en DB")
                    
                proy_id = res_proy.data[0]["id"]
                
                # B. Crear Tareas en Lote
                msg_calendar = []
                tareas_creadas = 0
                
                for t in tareas_lista:
                    # Preparar datos Supabase
                    data_t = {
                        "contenido": t.get("contenido"),
                        "fecha_limite": t.get("fecha_limite"), # YYYY-MM-DD
                        "hora_limite": t.get("hora"), # HH:MM
                        "es_habito": t.get("es_habito", False),
                        "frecuencia": t.get("frecuencia"),
                        "dias_semana": t.get("dias_semana", []),
                        "fecha_fin_habito": t.get("fecha_fin_habito"),
                        "proyecto_id": proy_id,
                        "estado": "pendiente"
                    }
                    
                    # Insertar Tarea
                    supabase.table("tareas").insert(data_t).execute()
                    tareas_creadas += 1
                    
                    # Sincronizar Calendario (Si tiene fecha)
                    if data_t["fecha_limite"]:
                        # Concatenar fecha + hora para el calendario si existe hora
                        fecha_final_iso = data_t["fecha_limite"]
                        if data_t["hora_limite"]:
                             # Simple combine string logic for now
                             fecha_final_iso = f"{data_t['fecha_limite']}T{data_t['hora_limite']}"
                        
                        try:
                            from modulos.calendario import add_event_to_calendar
                            # Add project name prefix to calendar event for context
                            summary_evt = f"[{nombre_proy}] {data_t['contenido']}"
                            if add_event_to_calendar(summary_evt, fecha_final_iso):
                                msg_calendar.append(t.get("contenido"))
                        except Exception:
                            pass

                # Respuesta final
                calendar_status = f"\n📅 {len(msg_calendar)} eventos agendados." if msg_calendar else ""
                return {
                    "messages": [AIMessage(content=f"✅ **Proyecto Iniciado:** '{nombre_proy}'\n\n🎯 Se han creado {tareas_creadas} tareas y {calendar_status}")],
                    "tarea_aprobada": False
                }

            except Exception as e:
                return {"messages": [AIMessage(content=f"❌ Error creando proyecto: {str(e)}")]}

    # --- 2. LEGACY TEXT PARSER (TAREAS ÚNICAS) ---
    last_content = last_ai_msg.content if hasattr(last_ai_msg, 'content') else ""
    if not "APROBADO:" in last_content and not "aprobado:" in last_content:
         # Should not happen if filtered correctly, but safety check
         return {"tarea_aprobada": False}

    # Parsear el mensaje estructurado
    # Formato esperado:
    # APROBADO: ...
    # DEADLINE: ...
    # HABIT: ...
    # DAYS: ...
    # END_DATE: ...
    
    lines = last_content.split('\n')
    contenido = ""
    fecha_limite = None
    hora_limite_val = None
    es_habito = False
    frecuencia = None
    dias_semana = []
    fecha_fin_habito = None
    
    for line in lines:
        if "APROBADO:" in line:
            contenido = line.replace("APROBADO:", "").strip()
        elif "DEADLINE:" in line:
            d_str = line.replace("DEADLINE:", "").strip()
            # Remove dash prefixes if any
            if d_str.startswith("-"):
                 d_str = d_str[1:].strip()
                 
            # Validation Logic
            # 1. Check if user explicitly said None/Ninguno
            is_explicit_none = d_str.lower().startswith("none") or d_str.lower().startswith("ningun")
            
            if d_str and not is_explicit_none:
                dt = dateparser.parse(d_str, settings={'PREFER_DATES_FROM': 'future'})
                if dt:
                    fecha_limite = dt.strftime("%Y-%m-%d %H:%M:%S%z") # ISO format
                else:
                    # VALIDATION FAILURE: Non-empty string that isn't a date
                    return {
                        "messages": [AIMessage(content=f"🤔 No entendí la fecha límite: '{d_str}'.\n\n¿Podrías decirme la fecha exacta (ej: 'Mañana', 'Lunes que viene' o '2026-05-20')?")],
                        "tarea_aprobada": False, # Bounce back to chat
                        "iteracion_socratica": state.get("iteracion_socratica", 0) + 1
                    }
                fecha_limite = None
        
        elif "DAYS:" in line:
            try:
                days_str = line.replace("DAYS:", "").strip(" []") # Remove brackets and label
                if days_str:
                    dias_semana = [int(x.strip()) for x in days_str.split(",") if x.strip().isdigit()]
            except:
                pass

        elif "END_DATE:" in line:
             ed_str = line.replace("END_DATE:", "").strip()
             if ed_str and not ed_str.lower().startswith("none"):
                 dt_ed = dateparser.parse(ed_str, settings={'PREFER_DATES_FROM': 'future'})
                 if dt_ed:
                     fecha_fin_habito = dt_ed.strftime("%Y-%m-%d")

        elif "TIME:" in line:
            t_str = line.replace("TIME:", "").strip()
            if t_str and not t_str.lower().startswith("none"):
                # Try parsing time
                try:
                    # Parse generic time string "20:00" or "8pm"
                    tt = dateparser.parse(t_str).time()
                    hora_limite_val = tt.strftime("%H:%M:%S")
                except:
                    hora_limite_val = None
            else:
                hora_limite_val = None

        elif "HABIT:" in line:
            h_str = line.replace("HABIT:", "").strip().lower()
            es_habito = (h_str == "true" or h_str == "sí" or h_str == "si")
        elif "FREQUENCY:" in line:
            f_str = line.replace("FREQUENCY:", "").strip()
            if f_str and not f_str.lower().startswith("none"):
                frecuencia = f_str

    if not contenido:
        return {
             "messages": [AIMessage(content="⚠️ No encontré la descripción de la tarea. ¿Podrías repetirla?")],
             "tarea_aprobada": False,
             "iteracion_socratica": state.get("iteracion_socratica", 0)
        }

    motivacion = state.get("motivacion_detectada", "")
    fase = state.get("fase_biologica", "Desconocida")
    
    # Merge Date + Time if both exist for the main Timestamp
    if hora_limite_val:
        from datetime import datetime
        if not fecha_limite:
            # Fallback: If time is set but date isn't (e.g. "At 8pm"), assume TODAY
            today_str = datetime.now().strftime("%Y-%m-%d")
            fecha_limite = today_str # Start with pure date string

        # Now merge time into date
        try:
             # Re-parse the date part
             dt_base = dateparser.parse(fecha_limite, settings={'PREFER_DATES_FROM': 'future'})
             # Parse the time part
             t_part = dateparser.parse(hora_limite_val).time()
             # Combine
             full_dt = dt_base.replace(hour=t_part.hour, minute=t_part.minute, second=0)
             fecha_limite = full_dt.strftime("%Y-%m-%d %H:%M:%S%z")
        except:
             pass 

    print(f"💾 Guardando en DB: {contenido} | Deadline: {fecha_limite} | Hora: {hora_limite_val}")

    # Insertar en Supabase
    try:
        data = {
            "contenido": contenido,
            "motivacion": motivacion,
            "fase_biologica": fase,
            "estado": "pendiente",
            "fecha_limite": fecha_limite,
            "es_habito": es_habito,
            "frecuencia": frecuencia,
            "dias_semana": dias_semana, # NEW
            "fecha_fin_habito": fecha_fin_habito, # NEW
            "hora_limite": hora_limite_val # SAVE SEPARATE TIME COLUMN
        }
        
        response = supabase.table("tareas").insert(data).execute()
        
        # 4. Sync to Google Calendar (if applicable)
        msg_calendar = ""
        if fecha_limite:
             try:
                 from modulos.calendario import add_event_to_calendar
                 # Use task content as summary, start time from fecha_limite
                 success = add_event_to_calendar(contenido, fecha_limite, duration_minutes=60)
                 if success:
                     msg_calendar = "\n📅 **Agenda:** Sincronizado con Google Calendar."
             except Exception as e:
                 print(f"⚠️ Failed to sync to Calendar: {e}")

        return {
            "messages": [AIMessage(content=f"✅ **Tarea guardada en tu Segundo Cerebro:**\n- {contenido}\n- Deadline: {fecha_limite or 'Ninguno'}\n- Hábito: {'Sí' if es_habito else 'No'}{msg_calendar}")],
            "tarea_aprobada": False, 
            "iteracion_socratica": 0,
            "motivacion_detectada": ""
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"❌ Error al guardar en base de datos: {str(e)}")]
        }

def get_resumen_diario() -> str:
    """
    Recupera un resumen de las tareas de hoy y hábitos para el contexto del Journaling.
    """
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # 1. Fetch Habits
        habits = supabase.table("tareas").select("contenido, estado").eq("es_habito", True).execute().data
        
        # 2. Fetch Tasks due Today (or overdue pending)
        # Note: Advanced date filtering in Supabase raw SQL might be better, but we'll try simple filtering here or rely on the agent to interpret.
        # Simple approach: fetch all pending and filter in python for now to avoid complex query string building issues
        active_tasks = supabase.table("tareas").select("contenido, fecha_limite, estado").neq("es_habito", True).execute().data
        
        relevant_tasks = []
        for t in active_tasks:
            fl = t.get("fecha_limite")
            if fl and fl.startswith(today_str):
                relevant_tasks.append(t)
        
        summary = f"📅 CONTEXTO DEL DÍA ({today_str}):\n\n"
        
        summary += "🔄 HÁBITOS:\n"
        for h in habits:
            status = "✅" if h["estado"] == "completado" else "⬜"
            summary += f"- {status} {h['contenido']}\n"
            
        summary += "\n🎯 TAREAS DE HOY:\n"
        if not relevant_tasks:
            summary += "(No hay tareas específicas para hoy)\n"
        for t in relevant_tasks:
            status = "✅" if t["estado"] == "completado" else "hz"
            summary += f"- {status} {t['contenido']}\n"

        # 3. Fetch Calendar Events
        from modulos.calendario import get_upcoming_events
        try:
            eventos = get_upcoming_events(5)
            if eventos:
                summary += "\n📅 AGENDA GOOGLE CALENDAR (Próximos):\n"
                for e in eventos:
                    start = e['start'].get('dateTime', e['start'].get('date'))
                    # Format simplified
                    summary += f"- {start}: {e.get('summary', 'Sin título')}\n"
        except Exception:
            summary += "\n(No se pudo conectar con Google Calendar)\n"
            
        return summary

    except Exception as e:
        return f"Error recuperando contexto: {str(e)}"
