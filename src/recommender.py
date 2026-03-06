from typing import List, Dict, Any
from src.llm_router import QueryRouter, QueryAnalysis, AssessmentReranker
from src.retriever import AssessmentRetriever

class AssessmentRecommender:
    """Orchestrates the Retrieve & Rerank (R&R) Hybrid Pipeline."""
    
    def __init__(self, router: QueryRouter, retriever: AssessmentRetriever, reranker: AssessmentReranker):
        self.router = router
        self.retriever = retriever
        self.reranker = reranker

    def _prepare_filters(self, analysis: QueryAnalysis) -> Dict[str, Any]:
        db_filters = {}
        if analysis.filters.remote_support and analysis.filters.remote_support not in ["None", "null"]:
            db_filters["remote_support"] = analysis.filters.remote_support
        if analysis.filters.adaptive_support and analysis.filters.adaptive_support not in ["None", "null"]:
            db_filters["adaptive_support"] = analysis.filters.adaptive_support
        if analysis.min_duration is not None:
            db_filters["min_duration"] = analysis.min_duration
        if analysis.max_duration is not None:
            db_filters["max_duration"] = analysis.max_duration
        return db_filters

    def _execute_search(self, search_query: str, filters: Dict[str, Any], fetch_k: int, requires_balance: bool) -> List[Dict[str, Any]]:
        final_results = []
        if requires_balance:
            k_half = fetch_k // 2
            tech_filters = filters.copy()
            tech_filters["test_types"] = "knowledge" 
            behav_filters = filters.copy()
            behav_filters["test_types"] = "personality"
            
            tech_results = self.retriever.retrieve(search_query, top_k=k_half, filters=tech_filters)
            behav_results = self.retriever.retrieve(search_query, top_k=k_half, filters=behav_filters)
            
            for i in range(max(len(tech_results), len(behav_results))):
                if i < len(tech_results): final_results.append(tech_results[i])
                if i < len(behav_results): final_results.append(behav_results[i])
        else:
            final_results = self.retriever.retrieve(search_query, top_k=fetch_k, filters=filters)
        return final_results

    def get_recommendations(self, raw_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        print(f"\n🚀 Processing Request: '{raw_query[:50]}...'")
        
        # --- 1. PRE-PROCESSING ---
        analysis = self.router.analyze(raw_query)
        word_count = len(raw_query.split())
        search_query = raw_query if word_count < 40 else analysis.refined_query
        base_filters = self._prepare_filters(analysis)
        
        # --- 2. BROAD RETRIEVAL ---
        fetch_k = top_k * 3 
        candidate_results = self._execute_search(search_query, base_filters, fetch_k, analysis.requires_balance)

        if not candidate_results and ("min_duration" in base_filters or "max_duration" in base_filters):
            print("⚠️ 0 results. Relaxing duration filters...")
            relaxed_filters = base_filters.copy()
            relaxed_filters.pop("min_duration", None)
            relaxed_filters.pop("max_duration", None)
            candidate_results = self._execute_search(search_query, relaxed_filters, fetch_k, analysis.requires_balance)

        # --- 3. POST-PROCESSING (RERANKING) ---
        if candidate_results:
            best_urls = self.reranker.rerank(raw_query, candidate_results, top_k)
            
            # Map the URLs back to the rich ChromaDB dictionaries
            final_results = []
            for url in best_urls:
                for res in candidate_results:
                    if res['url'] == url:
                        final_results.append(res)
                        break
            
            if not final_results:
                final_results = candidate_results[:top_k]
        else:
            final_results = []

        # --- 4. FORMATTING (EXACTLY THE SAME AS BEFORE) ---
        formatted_output = []
        for res in final_results[:top_k]:
            raw_types = res["metadata"].get("test_types", "")
            type_array = [t.strip() for t in raw_types.split(",")] if raw_types else []

            formatted_output.append({
                "url": res["url"],
                "name": res["name"],
                "adaptive_support": res.get("adaptive_support", "No"),
                "description": res["metadata"].get("description", ""),
                "duration": res.get("duration", 0),
                "remote_support": res.get("remote_support", "No"),
                "test_type": type_array
            })
            
        return formatted_output