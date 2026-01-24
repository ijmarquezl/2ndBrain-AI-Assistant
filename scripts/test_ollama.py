
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from modulos.coach_socratico import nodo_coach_socratico
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

def test_ollama_direct():
    print("🧪 Testing Direct Ollama Connection...")
    base_url = os.getenv("OLLAMA_BASE_URL")
    model = os.getenv("OLLAMA_MODEL")
    print(f"   URL: {base_url}")
    print(f"   Model: {model}")
    
    try:
        llm = ChatOllama(model=model, base_url=base_url)
        response = llm.invoke("Hola, ¿estás funcionando?")
        print(f"✅ Response received: {response.content}")
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")

def test_coach_node():
    print("\n🧪 Testing Coach Socratico Node (Ollama)...")
    state = {
        "messages": [HumanMessage(content="Quiero aprender a programar en Python")],
        "iteracion_socratica": 0
    }
    
    try:
        result = nodo_coach_socratico(state)
        print("\n✅ Node Execution Result:")
        print(f"Messages: {result['messages'][0].content}")
        print(f"Tarea Aprobada: {result.get('tarea_aprobada')}")
    except Exception as e:
        print(f"❌ Error executing node: {e}")

if __name__ == "__main__":
    test_ollama_direct()
    test_coach_node()
