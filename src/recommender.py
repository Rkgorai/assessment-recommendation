# from typing import List, Dict, Any
# from src.llm_router import QueryRouter, QueryAnalysis
# from src.retriever import AssessmentRetriever

# class AssessmentRecommender:
#     """Orchestrates the LLM routing and Vector DB retrieval."""
    
#     def __init__(self, router: QueryRouter, retriever: AssessmentRetriever):
#         self.router = router
#         self.retriever = retriever

#     def _prepare_filters(self, analysis: QueryAnalysis) -> Dict[str, Any]:
#         """Translates the LLM's JSON into strict ChromaDB filters."""
#         db_filters = {}
        
#         if analysis.filters.remote_support and analysis.filters.remote_support not in ["None", "null"]:
#             db_filters["remote_support"] = analysis.filters.remote_support
            
#         if analysis.filters.adaptive_support and analysis.filters.adaptive_support not in ["None", "null"]:
#             db_filters["adaptive_support"] = analysis.filters.adaptive_support

#         # 🚨 Use the durations directly extracted by the LLM
#         if analysis.min_duration is not None:
#             db_filters["min_duration"] = analysis.min_duration
#         if analysis.max_duration is not None:
#             db_filters["max_duration"] = analysis.max_duration

#         return db_filters

#     def get_recommendations(self, raw_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
#         print(f"\n🚀 Processing Request: '{raw_query[:50]}...'")
        
#         # 1. Single API call to the LLM to get everything
#         analysis = self.router.analyze(raw_query)
        
#         # 2. Use the LLM's summarized, keyword-rich query for the vector search
#         search_query = analysis.refined_query
#         print(f"🧠 LLM Refined Query: '{search_query}'")
        
#         # 3. Apply the LLM's extracted filters
#         base_filters = self._prepare_filters(analysis)
#         print(f"🔧 Prepared DB Filters: {base_filters}")
        
#         final_results = []
        
#         # 4. Execute Retrieval based on Domain Balance
#         if analysis.requires_balance:
#             print("⚖️ BALANCE REQUIRED: Splitting search into Technical and Behavioral domains.")
            
#             k_tech = (top_k // 2) + (top_k % 2) 
#             k_behav = top_k // 2
            
#             tech_filters = base_filters.copy()
#             tech_filters["test_types"] = "knowledge" 
#             tech_results = self.retriever.retrieve(search_query, top_k=k_tech, filters=tech_filters)
            
#             behav_filters = base_filters.copy()
#             behav_filters["test_types"] = "personality"
#             behav_results = self.retriever.retrieve(search_query, top_k=k_behav, filters=behav_filters)
            
#             # Interleave results
#             for i in range(max(len(tech_results), len(behav_results))):
#                 if i < len(tech_results):
#                     final_results.append(tech_results[i])
#                 if i < len(behav_results):
#                     final_results.append(behav_results[i])
                    
#         else:
#             print("🎯 STANDARD SEARCH: Executing single unified query.")
#             final_results = self.retriever.retrieve(search_query, top_k=top_k, filters=base_filters)

#         # 5. Format Output
#         formatted_output = []
#         for res in final_results[:top_k]:
#             raw_types = res["metadata"].get("test_types", "")
#             type_array = [t.strip() for t in raw_types.split(",")] if raw_types else []

#             formatted_output.append({
#                 "url": res["url"],
#                 "name": res["name"],
#                 "adaptive_support": res["adaptive_support"],
#                 "description": res["metadata"].get("description", ""),
#                 "duration": res["duration"],
#                 "remote_support": res["remote_support"],
#                 "test_type": type_array
#             })
            
#         return formatted_output

from typing import List, Dict, Any
from src.llm_router import QueryRouter, QueryAnalysis
from src.retriever import AssessmentRetriever

class AssessmentRecommender:
    """Orchestrates the LLM routing and Vector DB retrieval."""
    
    def __init__(self, router: QueryRouter, retriever: AssessmentRetriever):
        self.router = router
        self.retriever = retriever

    def _prepare_filters(self, analysis: QueryAnalysis) -> Dict[str, Any]:
        """Translates the LLM's JSON into strict ChromaDB filters."""
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

    def _execute_search(self, search_query: str, filters: Dict[str, Any], top_k: int, requires_balance: bool) -> List[Dict[str, Any]]:
        """Handles the actual retrieval, including domain balancing if required."""
        final_results = []
        
        if requires_balance:
            k_tech = (top_k // 2) + (top_k % 2) 
            k_behav = top_k // 2
            
            tech_filters = filters.copy()
            tech_filters["test_types"] = "knowledge" 
            tech_results = self.retriever.retrieve(search_query, top_k=k_tech, filters=tech_filters)
            
            behav_filters = filters.copy()
            behav_filters["test_types"] = "personality"
            behav_results = self.retriever.retrieve(search_query, top_k=k_behav, filters=behav_filters)
            
            # Interleave results
            for i in range(max(len(tech_results), len(behav_results))):
                if i < len(tech_results):
                    final_results.append(tech_results[i])
                if i < len(behav_results):
                    final_results.append(behav_results[i])
        else:
            final_results = self.retriever.retrieve(search_query, top_k=top_k, filters=filters)
            
        return final_results

    def get_recommendations(self, raw_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        print(f"\n🚀 Processing Request: '{raw_query[:50]}...'")
        
        # 1. Call the LLM Router
        analysis = self.router.analyze(raw_query)
        
        # 2. CHANGE #1: Dynamic Query Length Check (Threshold: ~40 words)
        word_count = len(raw_query.split())
        if word_count < 40:
            search_query = raw_query
            print(f"📝 Query is short ({word_count} words). Using RAW query for vector search.")
        else:
            search_query = analysis.refined_query
            print(f"🧠 Query is long ({word_count} words). Using LLM REFINED query: '{search_query}'")
        
        base_filters = self._prepare_filters(analysis)
        print(f"🔧 Prepared DB Filters: {base_filters}")
        
        # 3. First Search Attempt (Strict)
        final_results = self._execute_search(search_query, base_filters, top_k, analysis.requires_balance)

        # 4. CHANGE #2: Graceful Degradation (Fallback if 0 results and duration filters exist)
        has_duration_filters = "min_duration" in base_filters or "max_duration" in base_filters
        
        if not final_results and has_duration_filters:
            print("⚠️ 0 results found with strict time constraints. Relaxing duration filters...")
            relaxed_filters = base_filters.copy()
            # Pop removes the keys if they exist, ignoring them if they don't
            relaxed_filters.pop("min_duration", None)
            relaxed_filters.pop("max_duration", None)
            
            # Run the exact same search, just without the time constraints
            final_results = self._execute_search(search_query, relaxed_filters, top_k, analysis.requires_balance)

        # 5. Format Output
        formatted_output = []
        for res in final_results[:top_k]:
            raw_types = res["metadata"].get("test_types", "")
            type_array = [t.strip() for t in raw_types.split(",")] if raw_types else []

            formatted_output.append({
                "url": res["url"],
                "name": res["name"],
                "adaptive_support": res["adaptive_support"],
                "description": res["metadata"].get("description", ""),
                "duration": res["duration"],
                "remote_support": res["remote_support"],
                "test_type": type_array
            })
            
        return formatted_output