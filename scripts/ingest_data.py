import os
import sys
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document
from supabase.client import Client, create_client
from dotenv import load_dotenv

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

load_dotenv()

# Config
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Files to ingest
DATA_FILES = [
    "Atomic Habits by James Clear.pdf.pdf",
    "Brain-Rules.pdf",
    "Achievement_Habit.pdf",
    "Garcia Isra - Escuela De Estoicismo Moderno.epub"
]

def load_epub(path):
    """Custom lightweight EPUB loader using ebooklib + bs4"""
    print(f"📖 Processing EPUB: {path}")
    try:
        book = epub.read_epub(path)
        documents = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text()
                # Skip empty sections
                if text.strip():
                    documents.append(Document(page_content=text, metadata={"source": path}))
        return documents
    except Exception as e:
        print(f"❌ Error loading EPUB {path}: {e}")
        return []

def ingest_data():
    print(f"🚀 Starting ingestion process to SUPABASE using embeddings: Google Gemini (Cloud)")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in environment variables.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    documents = []
    
    for file_path in DATA_FILES:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            continue
            
        print(f"📚 Loading: {file_path}...")
        
        try:
            if file_path.lower().endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                documents.extend(docs)
                print(f"   - Loaded {len(docs)} pages.")
            elif file_path.lower().endswith(".epub"):
                docs = load_epub(file_path)
                documents.extend(docs)
                print(f"   - Loaded {len(docs)} chapters/sections.")
            else:
                print(f"⚠️ Unsupported format: {file_path}")
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")

    if not documents:
        print("❌ No documents loaded.")
        return

    print("✂️ Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   - Generated {len(chunks)} chunks.")

    print("💾 Creating Embeddings & Storing in Supabase (Local HuggingFace - Spanish Schema)...")
    from langchain_huggingface import HuggingFaceEmbeddings
    from core.supabase_extensions import SupabaseVectorStoreSpanish
    
    # Initialize Embedding Function (Local - Fast)
    embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Upload in chunks (Supabase has a payload limit, but no rate limit)
    BATCH_SIZE = 100 
    total_chunks = len(chunks)
    
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        print(f"   - Processing batch {i//BATCH_SIZE + 1}/{(total_chunks + BATCH_SIZE - 1)//BATCH_SIZE} ({len(batch)} chunks)...")
        
        try:
            SupabaseVectorStoreSpanish.from_documents(
                documents=batch,
                embedding=embedding_fn,
                client=supabase,
                table_name="documentos",
                query_name="buscar_documentos"
            )
        except Exception as e:
            print(f"❌ Error storing batch starting at {i}: {e}")

    print("✅ Ingestion Complete! Vectors stored in Supabase table 'documentos'.")


if __name__ == "__main__":
    ingest_data()
