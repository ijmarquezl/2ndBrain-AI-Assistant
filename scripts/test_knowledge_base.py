import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from modulos.nodo_base_conocimiento import nodo_base_conocimiento
from langchain_core.messages import HumanMessage

def test_knowledge_base():
    print("🧪 Testing Knowledge Base Node...")
    
    # Query about habits (should be in Atomic Habits)
    query = "Explain the four laws of behavior change."
    
    state = {
        "messages": [HumanMessage(content=query)],
        "modo_interaccion": "consulta"
    }
    
    try:
        result = nodo_base_conocimiento(state)
        response = result["messages"][0].content
        print("\n✅ Node Execution Result:")
        print(f"Agent Response:\n{response}")
        
    except Exception as e:
        print(f"\n❌ Error executing node: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_knowledge_base()
