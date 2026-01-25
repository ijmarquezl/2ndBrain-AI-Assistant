from langchain_huggingface import HuggingFaceEmbeddings

# Initialize Embedding (HuggingFace Local)
# Singleton instance to be shared across modules
embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
