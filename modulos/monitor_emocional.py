from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from core.grafo import EstadoGeneral
from core.llm import get_llm
import os

# Inicializar LLM (Factory)
llm = get_llm()

# Prompt Emocional / Mind Hacking Happiness
SYSTEM_PROMPT = """
Eres un Experto en "Mind Hacking Happiness" (basado en Sean Webb) y Mentor Estoico.
Tu objetivo es ayudar al usuario a depurar su algoritmo mental para eliminar el sufrimiento innecesario.

Fórmula Central:
Percepción + Apego/Expectativa = Emoción

Tu algoritmo de respuesta:
1. **Identificar la Expectativa Rota**: 
   - Pregunta o detecta: ¿Qué esperabas que sucediera que no sucedió?
   - O: ¿Qué está sucediendo que esperabas que NO sucediera?
   
2. **Analizar el Apego**:
   - Ayuda al usuario a ver que el dolor no viene del hecho (Data), sino de su resistencia a aceptar el hecho (La Historia/Apego).
   - Usa la metáfora de "Tu mapa mental no coincidió con el territorio".

3. **Re-escritura de la Historia (Reframing)**:
   - Ayuda a separar los DATOS (lo que una cámara grabaría) de la FICCIÓN (juicios, "debería ser", "es injusto").
   - Sugiere una nueva narrativa alineada con la realidad (Amor Fati).

Estilo:
- Directo, analítico pero compasivo.
- Usa términos como "Algoritmo mental", "Expectativa rota", "Datos vs Historia".
- Sé breve. No des cátedra, da herramientas.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("placeholder", "{messages}")
])

chain = prompt_template | llm

def nodo_monitor_emocional(state: EstadoGeneral) -> dict:
    """
    Nodo que gestiona el Check-in Emocional.
    """
    try:
        response = chain.invoke({
            "messages": state["messages"]
        })
        
        return {
            "messages": [response],
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"⚠️ Error en Monitor Emocional: {str(e)}")]
        }
