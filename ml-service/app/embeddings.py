from sentence_transformers import SentenceTransformer

_model = None

def get_embedding_model():
    """Lazily instantiates the embedding model."""
    global _model
    if _model is None:
        # Load local or download sentence-transformer model
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def generate_address_embedding(address_text: str) -> list:
    """Generates a 384-dimensional dense vector representing the address."""
    if not address_text:
        return []
        
    try:
        model = get_embedding_model()
        embedding = model.encode(address_text)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []
