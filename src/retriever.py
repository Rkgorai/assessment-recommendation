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
        test_type_filter = None
        
        if filters:
            conditions = []
            if "remote_support" in filters and filters["remote_support"]:
                conditions.append({"remote_support": filters["remote_support"]})
            if "adaptive_support" in filters and filters["adaptive_support"]:
                conditions.append({"adaptive_support": filters["adaptive_support"]})
            if "max_duration" in filters and filters["max_duration"]:
                conditions.append({"duration": {"$lte": filters["max_duration"]}})
            
            # Extract test_types so we can filter it safely in Python instead of ChromaDB
            if "test_types" in filters and filters["test_types"]:
                test_type_filter = filters["test_types"].lower()
            
            if len(conditions) == 1:
                where_clause = conditions[0]
            elif len(conditions) > 1:
                where_clause = {"$and": conditions} 

        query_embedding = self.embedding_manager.generate_embeddings([query])[0]
        
        # If we need to post-filter, grab extra results from the DB so we don't run out
        fetch_k = top_k * 5 if test_type_filter else top_k
        
        query_args = {"query_embeddings": [query_embedding.tolist()], "n_results": fetch_k}
        if where_clause:
            query_args["where"] = where_clause

        try:
            results = self.vector_store.collection.query(**query_args)
            
            retrieved_docs = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    metadata = results['metadatas'][0][i]
                    
                    # 🚨 BULLETPROOF PYTHON FILTER: Safely check if the category is in the metadata
                    if test_type_filter and test_type_filter not in str(metadata.get('test_types', '')).lower():
                        continue
                        
                    retrieved_docs.append({
                        'id': results['ids'][0][i],
                        'name': metadata['name'],
                        'url': metadata['url'],
                        'metadata': metadata,
                        'distance': results['distances'][0][i],
                        'duration': metadata.get('duration', 'N/A'),
                        'remote_support': metadata.get('remote_support', 'N/A'),
                        'adaptive_support': metadata.get('adaptive_support', 'N/A'),
                    })
                    
                    # Stop once we hit our exact target number
                    if len(retrieved_docs) >= top_k:
                        break
                        
            return retrieved_docs
            
        except Exception as e:
            print(f"❌ Error during retrieval: {e}")
            return []