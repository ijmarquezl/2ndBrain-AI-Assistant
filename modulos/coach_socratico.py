from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from core.grafo import EstadoGeneral
from core.llm import get_llm
import os
# from langchain_core.pydantic_v1 import BaseModel, Field # Deprecated/Removed in newer versions
from pydantic import BaseModel, Field
from typing import List, Optional

# Definición de Esquemas Pydantic
class TareaSchema(BaseModel):
    contenido: str = Field(description="Descripción accionable de la tarea")
    fecha_limite: Optional[str] = Field(description="YYYY-MM-DD o None si no se definió")
    hora: Optional[str] = Field(description="HH:MM o None si no es relevante")
    es_habito: bool = Field(description="True si es una tarea recurrente")
    frecuencia: Optional[str] = Field(description="Ej: Diario, Semanal, Mensual. None si es única.")
    dias_semana: List[int] = Field(default=[], description="Lista de días (0=Lunes, 6=Domingo) para hábitos semanales. Ej: [6] para 'todos los domingos'.")
    fecha_fin_habito: Optional[str] = Field(description="YYYY-MM-DD para finalizar el hábito. None si es indefinido.")

class PlanProyecto(BaseModel):
    """
    Estructura para registrar un Nuevo Proyecto con sus tareas planificadas.
    Invocar SOLO cuando el usuario haya aprobado explícitamente el plan.
    """
    nombre_proyecto: str = Field(description="Título corto y claro del proyecto")
    descripcion: str = Field(description="Resumen del objetivo y contexto")
    tareas: List[TareaSchema] = Field(description="Lista de tareas iniciales del proyecto")

# Inicializar LLM (usa Factory)
llm = get_llm()
# Bind Tools (Esto permite que el LLM decida cuando llamar a la función)
llm_with_tools = llm.bind_tools([PlanProyecto])

# Prompt Socrático
from datetime import datetime

# Fecha actual para contexto
current_date = datetime.now().strftime("%Y-%m-%d")
current_year = datetime.now().year

# Prompt Socrático
SYSTEM_PROMPT = f"""
Eres un Filósofo Estoico y Coach de Productividad (secweb 2.0).
Ayuda al usuario a definir tareas claras y PROYECTOS estructurados.
HOY ES: {current_date} (Año {current_year}).

CONTEXTO DE TAREAS ACTUALES:
{{contexto_tareas}}

ALGORITMO PRINCIPAL:
1. Dialoga socráticamente para clarificar objetivos.
2. Si es una TAREA ÚNICA o HÁBITO INDEFINIDO:
   - Sigue usando el formato de texto clásico:
     APROBADO: [Tarea]
     DEADLINE: [YYYY-MM-DD]
     TIME: [HH:MM]
     HABIT: [TRUE/FALSE]
     DAYS: [Lista de ints 0-6, ej: 0,2,4] (Solo si es Hábito Semanal INDEFINIDO)
     END_DATE: [YYYY-MM-DD] (Opcional, fin del hábito)

3. Si es un PROYECTO o RECURENCIA FINITA:
   - Si el usuario dice "Todos los domingos de Febrero" o "Las próximas 4 semanas":
     -> USA LA HERRAMIENTA `PlanProyecto`.
     -> CALCULA TÚ MISMO las fechas exactas (ej: 2026-02-01, 2026-02-08...) usando la fecha actual.
     -> Crea una TareaSchema por cada fecha específica.
   - Si es un objetivo grande que requiere pasos:
     -> Desglósalo y usa `PlanProyecto`.

MODO JOURNALING:
- Si recibes contexto del día y el usuario reflexiona, haz 3 preguntas profundas. No crees tareas.

REGLAS:
- NO inventes fechas.
- Se conciso y estoico.
- Para "todos los domingos" (indefinido), DAYS=[6], HABIT=TRUE.
- Para "todos los domingos DE FEBRERO" (finito), crea 4 tareas individuales con fecha exacta.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{messages}")
])

chain = prompt_template | llm_with_tools

from modulos.nodo_db import get_resumen_diario

def nodo_coach_socratico(state: EstadoGeneral) -> dict:
    """
    Nodo que ejecuta la lógica del Coach Socrático.
    """
    try:
        contexto = get_resumen_diario()
        
        response = chain.invoke({
            "messages": state["messages"],
            "contexto_tareas": contexto
        })
        
        # 1. Detectar Uso de Herramientas (Proyectos Pydantic)
        if response.tool_calls:
            print("🛠️ Tool Call Detected:", response.tool_calls[0]["name"])
            return {
                "messages": [response],
                "tarea_aprobada": True, # Pasamos a nodo_db para que ejecute la tool
                "motivacion_detectada": "Planificación de Proyecto"
            }

        content = response.content
        
        # 2. Detectar Formato Clásico (Tareas únicas)
        if "aprobado:" in content.lower():
            return {
                "messages": [response],
                "tarea_aprobada": True,
                "motivacion_detectada": content.replace("APROBADO:", "").replace("aprobado:", "").strip()
            }
        
        # 3. Conversación normal
        else:
            return {
                "messages": [response],
                "tarea_aprobada": False,
                "iteracion_socratica": state.get("iteracion_socratica", 0) + 1
            }

    except Exception as e:
        error_msg = f"⚠️ **El Coach Socrático está meditando (Error API):** {str(e)}"
        return {
            "messages": [AIMessage(content=error_msg)],
            "tarea_aprobada": False,
            "iteracion_socratica": state.get("iteracion_socratica", 0)
        }
