from core.llm import get_llm
from modulos.nodo_base_conocimiento import embedding_fn # This now points to HuggingFace
from core.supabase_extensions import SupabaseVectorStoreSpanish
from supabase.client import create_client, Client
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import random
import streamlit as st

# Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def generar_frase_estoica():
    """
    Generates a stoic/motivational quote using the RAG knowledge base.
    """
    try:
        # 1. Setup Retrieval
        llm = get_llm()
        
        if not (SUPABASE_URL and SUPABASE_KEY):
            return "La virtud es el único bien. (Modo Offline)"

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        vectorstore = SupabaseVectorStoreSpanish(
            client=supabase,
            embedding=embedding_fn,
            table_name="documentos",
            query_name="buscar_documentos"
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # 2. Randomize Topic slightly
        temas = ["disciplina", "resiliencia", "amor fati", "memento mori", "acción", "hábitos"]
        tema_del_dia = random.choice(temas)
        
        # 3. Retrieve Context
        docs = retriever.invoke(f"frase corta sobre {tema_del_dia}")
        context_text = "\n".join([d.page_content for d in docs])

        # 4. Generate Quote
        prompt = ChatPromptTemplate.from_template("""
        Eres un sabio estoico. Basándote en el siguiente contexto (o en tu conocimiento general de Estoicismo/Aikido si es insuficiente), 
        genera una frase CORTA, impactante y motivadora sobre: {tema}.
        Máximo 20 palabras. No uses hashtags.
        
        Contexto:
        {context}
        """)
        
        chain = prompt | llm | StrOutputParser()
        frase = chain.invoke({"tema": tema_del_dia, "context": context_text})
        
        return frase.replace('"', '')

    except Exception as e:
        print(f"Error generando frase: {e}")
        return "El obstáculo es el camino."
