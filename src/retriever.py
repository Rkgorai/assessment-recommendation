from typing import List, Dict, Any, Optional
from src.vector_store import VectorStore
from src.embeddings import EmbeddingManager

class AssessmentRetriever:
    """Handles query-based semantic retrieval and metadata filtering."""
    
    def __init__(self, vector_store: VectorStore, embedding_manager: EmbeddingManager):
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager

    def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        where_clause = None
        if filters:
            conditions = []
            if "remote_support" in filters and filters["remote_support"]:
                conditions.append({"remote_support": filters["remote_support"]})
            if "adaptive_support" in filters and filters["adaptive_support"]:
                conditions.append({"adaptive_support": filters["adaptive_support"]})
            if "max_duration" in filters and filters["max_duration"]:
                conditions.append({"duration": {"$lte": filters["max_duration"]}})
            if "test_types" in filters and filters["test_types"]:
                conditions.append({"test_types": {"$contains": filters["test_types"]}})
            
            if len(conditions) == 1:
                where_clause = conditions[0]
            elif len(conditions) > 1:
                where_clause = {"$or": conditions} # Using $or for better fallback

        query_embedding = self.embedding_manager.generate_embeddings([query])[0]
        query_args = {"query_embeddings": [query_embedding.tolist()], "n_results": top_k}
        if where_clause:
            query_args["where"] = where_clause

        results = self.vector_store.collection.query(**query_args)
        
        retrieved_docs = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                retrieved_docs.append({
                    'id': results['ids'][0][i],
                    'name': results['metadatas'][0][i]['name'],
                    'url': results['metadatas'][0][i]['url'],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
        return retrieved_docs