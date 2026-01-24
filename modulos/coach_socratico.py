from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from core.grafo import EstadoGeneral
from core.llm import get_llm
import os

# Inicializar LLM (usa Factory)
llm = get_llm()

# Prompt Socrático
from datetime import datetime

# Fecha actual para contexto
current_date = datetime.now().strftime("%Y-%m-%d")
current_year = datetime.now().year

# Prompt Socrático
SYSTEM_PROMPT = f"""
Eres un Filósofo Estoico y Coach de Productividad (secweb 2.0).
Ayuda al usuario a definir tareas claras, accionables y alineadas con sus valores.
HOY ES: {current_date} (Año {current_year}).

CONTEXTO DE TAREAS ACTUALES (Leído de la Base de Datos):
{{contexto_tareas}}

Tu algoritmo PRINCIPAL (Modo Tareas):
1. Si el usuario PREGUNTA qué tareas tiene, responde basándote en el CONTEXTO DE TAREAS. NO uses el formato APROBADO.
2. Si la tarea es vaga, pregunta PARA QUÉ (Values) y CÓMO (Implementation).
3. Si la tarea está clara, OBLIGATORIAMENTE verifica:
   - fecha límite ("¿Para cuándo es?") -> Si dice "no sé", asume None.
   - hora específica ("¿A qué hora?") -> Si es relevante para notificaciones.
   - recurrencia ("¿Es hábito?") -> Si no dice, asume No.
4. SOLO cuando tengas estos datos confirmados (o descartados), responde con el formato APROBADO.


---
MODO JOURNALING (Activado si recibes "CONTEXTO DEL DÍA"):
Si el mensaje contiene un resumen de actividades/hábitos:
1. Actúa como un Mentor Reflexivo (Estoico).
2. Analiza lo que completó (o falló) el usuario.
3. Genera EXACTAMENTE 3 preguntas profundas (pero breves) para ayudarle a reflexionar.
   - Ejemplo: "¿Qué obstáculo te impidió beber agua?", "¿Cómo te sentiste al terminar el informe?"
4. No uses el formato APROBADO/DEADLINE. Simplemente conversa.
---

⚠️ REGLAS CRÍTICAS DE VALIDACIÓN (Modo Tareas):
- NO apruebes si la fecha es ambigua (ej: "cuando pueda"). Pregunta una fecha específica.
- Si el usuario dice "sin fecha", escribe exactamente: DEADLINE: None
- Si especifica HORA (ej: "a las 4pm"), extráela en el campo TIME.

Formato de Respuesta Final (SOLO para Tareas):
APROBADO: [Descripción de la tarea]
DEADLINE: [YYYY-MM-DD o "None"]
TIME: [HH:MM o "None"]
HABIT: [TRUE/FALSE]
FREQUENCY: [Daily/Weekly/None]

Ejemplo:
User: "Voy a leer estoicismo"
Coach: "¿Qué libro y cuándo?"
User: "Leeré 10 páginas de Meditaciones hoy a las 20:00"
Coach: APROBADO: Leer 10 páginas de Meditaciones
DEADLINE: {current_year}-05-20
TIME: 20:00
HABIT: TRUE
FREQUENCY: Daily

NO inventes fechas pasadas. NO uses años anteriores a {current_year}. Si el usuario no dice, pon "None".
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{messages}")
])

chain = prompt_template | llm

from modulos.nodo_db import get_resumen_diario

def nodo_coach_socratico(state: EstadoGeneral) -> dict:
    """
    Nodo que ejecuta la lógica del Coach Socrático.
    """
    # Invocar cadena con manejo de errores
    try:
        # Obtener contexto fresco cada vez que el coach piensa
        contexto = get_resumen_diario()
        
        response = chain.invoke({
            "messages": state["messages"],
            "contexto_tareas": contexto
        })
        
        content = response.content
        
        # Lógica de aprobación simple basada en el texto
        if "aprobado:" in content.lower():
            return {
                "messages": [response],
                "tarea_aprobada": True,
                "motivacion_detectada": content.replace("APROBADO:", "").replace("aprobado:", "").strip()
            }
        else:
            # Incrementamos iteración (si quisiéramos limitar el loop)
            return {
                "messages": [response],
                "tarea_aprobada": False,
                "iteracion_socratica": state.get("iteracion_socratica", 0) + 1
            }

    except Exception as e:
        # Manejo elegante del error (Rate Limit u otros)
        error_msg = f"⚠️ **El Coach Socrático está meditando (Error API):** {str(e)}"
        
        # Retornamos un mensaje de error como si fuera del asistente para que se vea en el chat
        return {
            "messages": [AIMessage(content=error_msg)],
            "tarea_aprobada": False,
            "iteracion_socratica": state.get("iteracion_socratica", 0)
        }
