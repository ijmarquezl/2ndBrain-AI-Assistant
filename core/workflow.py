from langgraph.graph import StateGraph, END
from core.grafo import EstadoGeneral
from modulos.nodo_bio import nodo_bio_sync
from modulos.coach_socratico import nodo_coach_socratico
from modulos.nodo_db import nodo_db_saver
from modulos.monitor_emocional import nodo_monitor_emocional
from modulos.nodo_base_conocimiento import nodo_base_conocimiento

# Definir el Grafo
workflow = StateGraph(EstadoGeneral)

# Añadir Nodos
workflow.add_node("bio_sync", nodo_bio_sync)
workflow.add_node("coach_socratico", nodo_coach_socratico)
workflow.add_node("monitor_emocional", nodo_monitor_emocional)
workflow.add_node("base_conocimiento", nodo_base_conocimiento)
workflow.add_node("db_saver", nodo_db_saver)

# Definir Punto de Entrada
workflow.set_entry_point("bio_sync")

# Definir Edges Condicionales
def router_bio(state: EstadoGeneral):
    # Si el bio-sync rechazó la tarea (es_valida=False implicitamente si tarea_aprobada es False y venimos de bio),
    # pero necesitamos distinguir si fue rechazo bio o solo passthrough.
    # Revisamos el último mensaje. Si es una ALERTA de bio-sync, terminamos.
    last_msg = state["messages"][-1]
    if "ALERTA DE HACKEO MENTAL" in last_msg.content or "Estás en periodo de Ayuno" in last_msg.content:
        return END
        
    # Router Principal: ¿Es Tarea o Check-in Emocional?
    modo = state.get("modo_interaccion", "tarea")
    
    if modo == "emocional":
        return "monitor_emocional"
    elif modo == "consulta":
        return "base_conocimiento"
    else:
        return "coach_socratico"

workflow.add_conditional_edges(
    "bio_sync",
    router_bio,
    {
        END: END,
        "coach_socratico": "coach_socratico",
        "monitor_emocional": "monitor_emocional",
        "base_conocimiento": "base_conocimiento"
    }
)

def router_coach(state: EstadoGeneral):
    if state.get("tarea_aprobada"):
        return "db_saver" # Guardamos en DB
    return END # Sigue preguntando (loop termina por ahora, espera input usuario)

# Conexiones
workflow.add_conditional_edges(
    "coach_socratico",
    router_coach,
    {
        "db_saver": "db_saver",
        END: END
    }
)

workflow.add_edge("db_saver", END)
workflow.add_edge("monitor_emocional", END)
workflow.add_edge("base_conocimiento", END)

# Compilar
app_graph = workflow.compile()
