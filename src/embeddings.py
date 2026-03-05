import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

class EmbeddingManager:
    """Handles embedding generation using HuggingFace SentenceTransformers."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        print(f"⚙️ Loading Embedding model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        print(f"✅ Embedding model loaded. Dimension: {self.model.get_sentence_embedding_dimension()}")

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        if not self.model:
            raise ValueError("Model not loaded")
        return self.model.encode(texts, show_progress_bar=False)