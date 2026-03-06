import os
import numpy as np
from typing import List, Dict, Any
import chromadb

class VectorStore:
    """Manages the ChromaDB persistent vector store."""
    
    def __init__(self, collection_name: str = "shl_assessments", persist_directory: str = "../database/chroma_db"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._initialize_store()

    def _initialize_store(self):
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "description": "SHL Assessment Catalog",
                "hnsw:space": "cosine" 
            }
        )
        print(f"✅ Vector store ready. Documents: {self.collection.count()}")

    def add_assessments(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str], embeddings: np.ndarray):
        print(f"💾 Upserting {len(documents)} assessments...")
        self.collection.upsert(
            ids=ids,
            metadatas=metadatas,
            documents=documents,
            embeddings=embeddings.tolist()
        )