
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from modulos.monitor_emocional import nodo_monitor_emocional
from langchain_core.messages import HumanMessage

def test_monitor_emocional():
    print("🧪 Testing Emotional Monitor Node...")
    
    # Mock state with "stress" input
    state = {
        "messages": [
            HumanMessage(content="Estoy muy enojado porque mi compañero no entregó el reporte a tiempo y me hizo quedar mal.")
        ],
        "modo_interaccion": "emocional"
    }
    
    try:
        result = nodo_monitor_emocional(state)
        response = result["messages"][0].content
        print("\n✅ Node Execution Result:")
        print(f"Agent Response:\n{response}")
        
        # Simple string check for key stoic concepts or reframing
        if "re-encuadre" in response.lower() or "control" in response.lower() or "historia" in response.lower():
            print("\n✅ Stoic concepts detected.")
        else:
             print("\n⚠️ Warning: Stoic keywords not explicitly found, check output quality.")
        
    except Exception as e:
        print(f"\n❌ Error executing node: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monitor_emocional()
