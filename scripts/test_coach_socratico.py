
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from modulos.coach_socratico import nodo_coach_socratico
from langchain_core.messages import HumanMessage

def test_coach_socratico():
    print("🧪 Testing Coach Socratico with simple task...")
    
    # Simulate state
    state = {
        "messages": [HumanMessage(content="Quiero comprar un coche nuevo")],
        "iteracion_socratica": 0
    }
    
    try:
        result = nodo_coach_socratico(state)
        print("\n✅ Result received:")
        print(f"Messages: {result['messages'][0].content}")
        print(f"Tarea Aprobada: {result.get('tarea_aprobada')}")
        print(f"Motivacion: {result.get('motivacion_detectada')}")
        
    except Exception as e:
        print(f"\n❌ Error executing node: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coach_socratico()
