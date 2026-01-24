from core.grafo import EstadoGeneral
from modulos.bio_sync import obtener_fase_actual, analizar_alineacion_tarea
from langchain_core.messages import AIMessage

def nodo_bio_sync(state: EstadoGeneral) -> dict:
    """
    Nodo que verifica la fase biológica antes de pasar al coach.
    """
    # Obtenemos el último mensaje del usuario
    ult_mensaje = state["messages"][-1].content
    
    # 1. Detectar Fase
    fase = obtener_fase_actual()
    
    # 2. Analizar Alineación
    analisis = analizar_alineacion_tarea(ult_mensaje, fase)
    
    if not analisis["es_valida"]:
        # Si falla el Bio-Sync, interrumpimos con un mensaje del sistema
        # y marcamos la tarea como NO aprobada para que no pase al Coach (o pase con warning)
        # En este diseño, si falla bio-sync, devolvemos respuesta final directa.
        return {
            "messages": [AIMessage(content=analisis["mensaje"])],
            "fase_biologica": fase,
            "tarea_aprobada": False
        }
    
    # Si es válida, pasamos al siguiente nodo (Coach)
    return {
        "fase_biologica": fase,
        # No añadimos mensaje aquí, dejamos que el Coach hable
    }
