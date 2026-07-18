try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False

_model = None

def get_embedding_model():
    """Lazily instantiates the embedding model."""
    global _model
    if not HAS_ST:
        return None
    if _model is None:
        try:
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Could not load SentenceTransformer: {e}")
            _model = None
    return _model

def generate_address_embedding(address_text: str) -> list:
    """Generates a 384-dimensional dense vector representing the address."""
    if not address_text:
        return []
        
    try:
        model = get_embedding_model()
        if model is None:
            return []
        embedding = model.encode(address_text)
        return embedding.tolist()
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []
