import os
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """
    Factory function to return the configured LLM.
    Prioritizes Groq if API Key is present, otherwise falls back to local Ollama.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
    
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")

    if groq_api_key and groq_model:
        # print(f"🚀 Using Groq LLM: {groq_model}") # Debug info
        return ChatGroq(
            temperature=0.3,
            model_name=groq_model,
            groq_api_key=groq_api_key
        )
    else:
        # print(f"🦙 Using Local Ollama: {ollama_model}") # Debug info
        return ChatOllama(
            model=ollama_model,
            base_url=ollama_base_url,
            temperature=0.3
        )
