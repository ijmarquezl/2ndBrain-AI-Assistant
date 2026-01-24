
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from modulos.nodo_db import nodo_db_saver
from langchain_core.messages import HumanMessage, AIMessage

def test_db_saver():
    print("🧪 Testing DB Saver Node...")
    
    # Mock state
    state = {
        "messages": [
            HumanMessage(content="Quiero aprender guitarra"),
            AIMessage(content="¿Por qué?"),
            HumanMessage(content="Para tocar canciones a mis amigos")
        ],
        "iteracion_socratica": 2,
        "tarea_aprobada": True,
        "motivacion_detectada": "Conexión social y expresión artística",
        "fase_biologica": "Fase Productiva"
    }
    
    try:
        result = nodo_db_saver(state)
        print("\n✅ Node Execution Result:")
        print(f"Messages: {result['messages'][0].content}")
        
    except Exception as e:
        print(f"\n❌ Error executing node: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_saver()
