import os
from langchain_groq import ChatGroq
# from langchain_ollama import ChatOllama # Removed hard dependency
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    """
    Factory function to return the configured LLM.
    Prioritizes Groq if API Key is present, otherwise falls back to local Ollama.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Fallback: Check Streamlit Secrets (for Streamlit Cloud)
    if not groq_api_key:
        try:
            import streamlit as st
            # DEBUG: Print keys (masked) to logs
            # print(f"DEBUG: Secrets Keys Available: {list(st.secrets.keys())}")
            
            if "GROQ_API_KEY" in st.secrets:
                groq_api_key = st.secrets["GROQ_API_KEY"]
                print("✅ Found GROQ_API_KEY in st.secrets")
                # Also try to get model from secrets or default
                groq_model = st.secrets.get("GROQ_MODEL", groq_model)
            else:
                print("❌ GROQ_API_KEY NOT found in st.secrets")
                # Handle nested secrets (common in TOML) e.g. [groq] api_key = ...
                if "groq" in st.secrets and "api_key" in st.secrets["groq"]:
                     groq_api_key = st.secrets["groq"]["api_key"]
                     print("✅ Found GROQ_API_KEY in st.secrets['groq']['api_key']")

        except (ImportError, FileNotFoundError):
            print("⚠️ Streamlit secrets not accessible")
            pass # Not running in Streamlit or no secrets found

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
        # Lazy import to avoid crashing in cloud environments where Ollama isn't installed
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=ollama_model,
                base_url=ollama_base_url,
                temperature=0.3
            )
        except ImportError:
            raise ImportError("Ollama libraries not found. Install 'langchain-ollama' or set GROQ_API_KEY for cloud use.")
