from typing import TypedDict, List, Annotated
import operator
from langchain_core.messages import BaseMessage

class EstadoGeneral(TypedDict):
    """
    Estado global del grafo para el Segundo Cerebro.
    """
    # Historial de mensajes (LangChain format)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Datos de contexto
    fase_biologica: str
    
    # Estado del flujo socrático
    intento_tarea: str
    iteracion_socratica: int  # Contador para no preguntar infinitamente
    motivacion_detectada: str # El "porqué" raíz
    
    # Flags de control
    tarea_aprobada: bool
    modo_interaccion: str # "tarea" o "emocional"
