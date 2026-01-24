import streamlit as st
import os
from dotenv import load_dotenv
from modulos.bio_sync import obtener_fase_actual, analizar_alineacion_tarea, sugerir_accion_fase

# Cargar variables de entorno
load_dotenv()

st.set_page_config(
    page_title="2ndBrain - Segundo Cerebro Estoico",
    page_icon="🧠",
    layout="wide"
)

def main():
    st.title("🧠 2ndBrain: Asistente Personal Estoico")
    
    # --- Sidebar: Bio-Sync Mood ---
    fase_actual = obtener_fase_actual()
    st.sidebar.header("🕒 Bio-Sincronización")
    st.sidebar.markdown(f"**Fase Actual**: `{fase_actual}`")
    
    # Sugerencia de acción
    sugerencia = sugerir_accion_fase(fase_actual)
    st.sidebar.info(sugerencia)

    # --- Motivation Sidebar ---
    from modulos.motivacion import generar_frase_estoica
    from modulos.nodo_db import get_resumen_diario # Import helper
    
    st.sidebar.header("💡 Sabiduría del Día")
    if st.sidebar.button("Nueva Frase"):
        st.cache_data.clear()
        
    st.sidebar.markdown("---")
    st.sidebar.header("✍️ Diario Estoico")
    if st.sidebar.button("Iniciar Reflexión"):
        # 1. Get Context
        contexto = get_resumen_diario()
        # 2. Inject Message
        st.session_state.messages.append({
            "role": "user", 
            "content": f"Quiero hacer mi reflexión del día. Aquí está mi resumen:\n\n{contexto}"
        })
        st.rerun()
    
    frase = generar_frase_estoica()
    st.sidebar.warning(f"_{frase}_")
    
    # --- Selector de Modo ---
    st.sidebar.header("🛠️ Modo")
    modo_seleccionado = st.sidebar.radio(
        "Elige tu interacción:",
        ["Coach de Tareas", "Monitor Emocional", "Consultar Segundo Cerebro"],
        index=0
    )
    
    # Mapear selección a valor interno
    mapa_modos = {
        "Coach de Tareas": "tarea",
        "Monitor Emocional": "emocional",
        "Consultar Segundo Cerebro": "consulta"
    }
    modo_interno = mapa_modos[modo_seleccionado]
    
    # --- Verificaciones de Entorno ---
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("⚠️ Falta configurar GOOGLE_API_KEY en el archivo .env")
        st.stop()

    st.markdown("""
    > *"No es que tengamos poco tiempo, sino que perdemos mucho."* — Séneca
    """)
    
    # Placeholder para el chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Placeholder dinámico según modo
    placeholders = {
        "Coach de Tareas": "¿Qué tarea quieres lograr hoy?",
        "Monitor Emocional": "¿Cómo te sientes? (Check-in)",
        "Consultar Segundo Cerebro": "Pregunta a tu biblioteca personal..."
    }
    input_text = placeholders.get(modo_seleccionado, "¿Qué quieres procesar?")

    if prompt := st.chat_input(input_text):
        # Mostrar mensaje usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Invocar LangGraph
        from core.workflow import app_graph
        from langchain_core.messages import HumanMessage
        
        with st.chat_message("assistant"):
            with st.spinner("🧠 Procesando con 2ndBrain..."):
                # Ejecutar grafo
                # Construir historial con ventana de contexto (últimos 5 mensajes + actual)
                history = []
                # Tomamos los últimos 4 mensajes del historial (para sumar al actual y dar 5 aprox)
                recent_msgs = st.session_state.messages[-4:] 
                
                from langchain_core.messages import HumanMessage, AIMessage
                
                for msg in recent_msgs:
                    if msg["role"] == "user":
                        history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        history.append(AIMessage(content=msg["content"]))
                
                # Agregar mensaje actual
                history.append(HumanMessage(content=prompt))
                
                # Cargar estado previo del grafo (si existe)
                previous_state = st.session_state.get("graph_state", {})
                
                inputs = {
                    "messages": history,
                    "iteracion_socratica": previous_state.get("iteracion_socratica", 0),
                    "tarea_aprobada": previous_state.get("tarea_aprobada", False),
                    "motivacion_detectada": previous_state.get("motivacion_detectada", ""),
                    "modo_interaccion": modo_interno
                }
                
                # Usamos invoke por simplicidad en MVP (no streaming aún)
                final_state = app_graph.invoke(inputs)
                
                # Persistir estado actualizado en sesión
                st.session_state.graph_state = final_state
                
                # Obtener última respuesta del asistente
                last_msg = final_state["messages"][-1]
                response_content = last_msg.content
                
                st.markdown(response_content)
        
        # Guardar respuesta en historial
        st.session_state.messages.append({"role": "assistant", "content": response_content})

if __name__ == "__main__":
    main()
