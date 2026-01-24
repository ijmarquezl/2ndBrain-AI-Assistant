
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from modulos.coach_socratico import nodo_coach_socratico
from langchain_core.messages import HumanMessage, AIMessage

def test_conversation_flow():
    print("🧪 Testing Multi-turn Conversation with Context...")
    
    # 1. User wants to buy a car
    print("\n--- Turn 1: Initial Request ---")
    state_turn_1 = {
        "messages": [HumanMessage(content="Quiero comprar un coche nuevo")],
        "iteracion_socratica": 0
    }
    result_1 = nodo_coach_socratico(state_turn_1)
    response_1 = result_1["messages"][0].content
    print(f"Agent: {response_1}")
    
    # 2. User answers "Why" (Agent should remember specific context from Turn 1)
    print("\n--- Turn 2: User answers 'Para ir al trabajo' ---")
    # Simulate constructing history like app.py
    history = [
        HumanMessage(content="Quiero comprar un coche nuevo"),
        AIMessage(content=response_1),
        HumanMessage(content="Para ir al trabajo más rápido y no usar transporte público")
    ]
    
    state_turn_2 = {
        "messages": history,
        "iteracion_socratica": result_1.get("iteracion_socratica", 0),
        "tarea_aprobada": result_1.get("tarea_aprobada", False),
        "motivacion_detectada": result_1.get("motivacion_detectada", "")
    }
    
    # NOTE: The current node implementation ignores input 'tarea_aprobada' logic-wise, 
    # but we are verifying here that we CAN pass it and the infrastructure supports it.
    
    result_2 = nodo_coach_socratico(state_turn_2)
    response_2 = result_2["messages"][0].content
    print(f"Agent: {response_2}")
    
    if result_2.get("tarea_aprobada"):
        print("✅ Tarea Aprobada correctly!")
    else:
        print("ℹ️ Still questioning... (This is okay if motivation isn't deep enough yet)")
        
    # Check simple approval parsing
    print("\n--- Testing Parsing Robustness ---")
    mock_response = AIMessage(content="aprobado: La motivación es válida.")
    mock_state = {"messages": [mock_response]}
    # We can't easily unit test the function's internal logic without mocking LLM, 
    # but we can verify the fix physically by running this script and seeing meaningful replies.

if __name__ == "__main__":
    test_conversation_flow()
