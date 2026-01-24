from langchain_community.vectorstores import SupabaseVectorStore
from core.supabase_extensions import SupabaseVectorStoreSpanish
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from core.grafo import EstadoGeneral
from core.llm import get_llm
from supabase.client import Client, create_client
import os

# Configuración
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Inicializar LLM
llm = get_llm()

# Inicializar Embedding (HuggingFace Local)
embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Inicializar Supabase Vector Store
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    vectorstore = SupabaseVectorStoreSpanish(
        client=supabase,
        embedding=embedding_fn,
        table_name="documentos",
        query_name="buscar_documentos"
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
else:
    vectorstore = None
    retriever = None

# Prompt RAG
RAG_PROMPT = """
Eres el Bibliotecario del Segundo Cerebro Personal.
Tu misión es responder preguntas basándote ESTRICTAMENTE en el contexto proporcionado.
El contexto proviene de: "Atomic Habits", "Brain Rules", y filosofia Estoica/Aikido.

Reglas:
1. Usa solo la información del Contexto para responder.
2. Si la respuesta no está en el contexto, di "No encuentro información sobre eso en tu Base de Conocimiento personal".
3. Cita el libro o concepto si es evidente.

Contexto:
{context}

Pregunta del Usuario:
{question}
"""

prompt_template = ChatPromptTemplate.from_template(RAG_PROMPT)
chain = prompt_template | llm

def nodo_base_conocimiento(state: EstadoGeneral) -> dict:
    """
    Nodo RAG: Busca en vector store y genera respuesta.
    """
    if not retriever:
        return {"messages": [AIMessage(content="⚠️ Error: Base de conocimiento no inicializada. Por favor ejecuta el script de ingestión.")]}
    
    # Obtener última pregunta
    last_msg = state["messages"][-1].content
    
    try:
        # 1. Retrieve
        docs = retriever.invoke(last_msg)
        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 2. Augment & Generate
        response = chain.invoke({
            "context": context_text,
            "question": last_msg
        })
        
        return {
            "messages": [response]
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"❌ Error en RAG: {str(e)}")]
        }
