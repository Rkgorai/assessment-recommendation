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
        if llm_filters.remote_support and llm_filters.remote_support not in ["None", "null"]:
            db_filters["remote_support"] = llm_filters.remote_support
        if llm_filters.adaptive_support and llm_filters.adaptive_support not in ["None", "null"]:
            db_filters["adaptive_support"] = llm_filters.adaptive_support
        if llm_filters.max_duration and str(llm_filters.max_duration).isdigit():
            db_filters["max_duration"] = int(llm_filters.max_duration)
        return db_filters

    def get_recommendations(self, raw_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        print(f"\n🚀 Processing Request: '{raw_query[:50]}...'")
        
        analysis = self.router.analyze(raw_query)
        search_query = analysis.search_query
        base_filters = self._prepare_filters(analysis.filters)
        
        final_results = []
        
        if analysis.requires_balance:
            print("⚖️ BALANCE REQUIRED: Splitting search into Technical and Behavioral domains.")
            
            k_tech = (top_k // 2) + (top_k % 2) 
            k_behav = top_k // 2
            
            # Use lowercase root words for the safe Python filter
            tech_filters = base_filters.copy()
            tech_filters["test_types"] = "knowledge" 
            tech_results = self.retriever.retrieve(search_query, top_k=k_tech, filters=tech_filters)
            
            behav_filters = base_filters.copy()
            behav_filters["test_types"] = "personality"
            behav_results = self.retriever.retrieve(search_query, top_k=k_behav, filters=behav_filters)
            
            # Interleave results
            for i in range(max(len(tech_results), len(behav_results))):
                if i < len(tech_results):
                    final_results.append(tech_results[i])
                if i < len(behav_results):
                    final_results.append(behav_results[i])
                    
        else:
            print("🎯 STANDARD SEARCH: Executing single unified query.")
            final_results = self.retriever.retrieve(search_query, top_k=top_k, filters=base_filters)

        formatted_output = []
        for res in final_results[:top_k]:
            formatted_output.append({
                "name": res["name"],
                "url": res["url"],
                "test_types": res['metadata']['test_types'],
                "duration": res.get("duration", "N/A"),
                "remote_support": res.get("remote_support", "N/A"),
                "adaptive_support": res.get("adaptive_support", "N/A")
            })

            # print("!!!!!!!!!!res:", res)
            
        return formatted_output