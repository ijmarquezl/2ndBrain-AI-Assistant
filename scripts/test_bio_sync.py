import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from modulos.bio_sync import obtener_fase_actual, analizar_alineacion_tarea

def test_bio_sync():
    print("🧠 Iniciando Pruebas de Bio-Sync...\n")
    
    casos_prueba = [
        ("09:30", "Ventana de Cetosis", "administrativa"),
        ("09:30", "Ventana de Cetosis", "escribir libro"),
        ("14:00", "Alimentación", "comida"),
        ("22:00", "Ayuno", "cenar tarde"),
        ("06:00", "Ayuno", "meditar")
    ]
    
    for hora_str, fase_esperada, tarea in casos_prueba:
        # Mockear hora
        hora_mock = datetime.strptime(hora_str, "%H:%M")
        fase_detectada = obtener_fase_actual(hora_mock)
        
        print(f"🕒 Hora: {hora_str} | Fase: {fase_detectada}")
        assert fase_detectada == fase_esperada, f"Error: Esperaba {fase_esperada}, obtuve {fase_detectada}"
        
        analisis = analizar_alineacion_tarea(tarea, fase_detectada)
        print(f"   Tarea: '{tarea}' -> {analisis['mensaje']}")
        print("-" * 30)

    print("\n✅ Todas las pruebas pasaron correctamente.")

if __name__ == "__main__":
    test_bio_sync()
