from datetime import datetime, time

# Definición de fases
FASE_AYUNO = "Ayuno"
FASE_CETOSIS = "Ventana de Cetosis"
FASE_ALIMENTACION = "Alimentación"

def obtener_fase_actual(hora_actual: datetime = None) -> str:
    """
    Determina la fase biológica actual basada en la hora.
    - Ventana de Cetosis: 08:00 - 11:00 (Máximo rendimiento)
    - Ayuno: 20:00 - 11:00 (Incluye la ventana de cetosis, pero se distingue por prioridad)
    - Alimentación: 11:00 - 20:00
    """
    if hora_actual is None:
        hora_actual = datetime.now()
    
    current_time = hora_actual.time()
    
    # 08:00 - 11:00 -> Prioridad Máxima: Ventana de Cetosis
    if time(8, 0) <= current_time < time(11, 0):
        return FASE_CETOSIS
    
    # 11:00 - 20:00 -> Ventana de Alimentación
    if time(11, 0) <= current_time < time(20, 0):
        return FASE_ALIMENTACION
        
    # Resto (20:00 - 08:00) -> Ayuno
    return FASE_AYUNO

def analizar_alineacion_tarea(tipo_tarea: str, fase_actual: str) -> dict:
    """
    Verifica si una tarea es adecuada para la fase actual.
    """
    tipo_tarea = tipo_tarea.lower()
    
    if fase_actual == FASE_CETOSIS:
        if any(t in tipo_tarea for t in ["administrativa", "baja energía", "rutina", "pagos", "emails"]):
            return {
                "es_valida": False,
                "mensaje": "⚠️ ALERTA DE HACKEO MENTAL: Estás en tu 'Ventana de Cetosis' (Máximo Rendimiento). No desperdicies glucosa cerebral en tareas triviales. Mueve esto a la tarde."
            }
        return {
            "es_valida": True,
            "mensaje": "🔥 ¡Excelente! Hora de Deep Work."
        }
        
    if fase_actual == FASE_AYUNO and "comida" in tipo_tarea:
         return {
            "es_valida": False,
            "mensaje": "⛔ Estás en periodo de Ayuno. Recuerda tu objetivo: Autofagia y Claridad Mental. Espera a las 11:00."
        }
        
    return {"es_valida": True, "mensaje": "✅ Tarea registrada."}

def sugerir_accion_fase(fase: str) -> str:
    """Devuelve un consejo corto basado en la fase actual."""
    if fase == FASE_CETOSIS:
        return "🧠 Foco Total: Prioriza tareas estratégicas o creativas."
    elif fase == FASE_AYUNO:
        return "💧 Mantente hidratado. Tareas de mantenimiento o descanso."
    elif fase == FASE_ALIMENTACION:
        return "⚡ Energía disponible. Buen momento para ejecución física o reuniones."
    return "Neutral."
