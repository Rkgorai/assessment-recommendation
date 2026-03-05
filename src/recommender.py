from typing import List, Dict, Any
from src.llm_router import QueryRouter, AssessmentFilters
from src.retriever import AssessmentRetriever

class AssessmentRecommender:
    """Orchestrates the LLM routing and Vector DB retrieval."""
    
    def __init__(self, router: QueryRouter, retriever: AssessmentRetriever):
        self.router = router
        self.retriever = retriever

    def _prepare_filters(self, llm_filters: AssessmentFilters) -> Dict[str, Any]:
        db_filters = {}
        if llm_filters.remote_support:
            db_filters["remote_support"] = llm_filters.remote_support
        if llm_filters.adaptive_support:
            db_filters["adaptive_support"] = llm_filters.adaptive_support
        if llm_filters.max_duration:
            try:
                # Safely cast string "40" to integer 40 for ChromaDB math
                db_filters["max_duration"] = int(llm_filters.max_duration)
            except ValueError:
                pass 
        return db_filters

    def get_recommendations(self, raw_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        analysis = self.router.analyze(raw_query)
        search_query = analysis.search_query
        base_filters = self._prepare_filters(analysis.filters)
        
        final_results = self.retriever.retrieve(search_query, top_k=top_k, filters=base_filters)

        formatted_output = []
        for res in final_results[:top_k]:
            formatted_output.append({
                "name": res["name"],
                "url": res["url"],
                "test_type": {res['metadata']['test_types']},
                "duration": f"{res['metadata']['duration']} mins",
                "remote_support": res['metadata'].get('remote_support', 'N/A'),
                "adaptive_support": res['metadata'].get('adaptive_support', 'N/A'),
                "description": res['metadata'].get('description', 'No description available.')
            })
            
        return formatted_output