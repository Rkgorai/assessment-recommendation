from typing import List, Dict, Any
from src.llm_router import QueryRouter, AssessmentFilters
from src.retriever import AssessmentRetriever
import re

class AssessmentRecommender:
    """Orchestrates the LLM routing and Vector DB retrieval."""
    
    def __init__(self, router: QueryRouter, retriever: AssessmentRetriever):
        self.router = router
        self.retriever = retriever

    def _extract_time_from_query(self, query: str) -> tuple[int, int]:
        """Bulletproof Python RegEx to extract time ranges and convert hours to minutes."""
        query = query.lower()
        min_val, max_val = None, None

        # 1. Look for ranges: "30-40 mins", "1-2 hours", "30 to 40 minutes"
        range_match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)\s*(min|hour|hr)', query)
        if range_match:
            min_val, max_val = int(range_match.group(1)), int(range_match.group(2))
            if 'hour' in range_match.group(3) or 'hr' in range_match.group(3):
                min_val *= 60
                max_val *= 60
            return min_val, max_val
        
        # 2. Look for Max caps: "under 40", "in 40", "less than 40"
        max_match = re.search(r'(?:under|in|max|less than|maximum)\s*(\d+)\s*(min|hour|hr)?', query)
        if max_match:
            max_val = int(max_match.group(1))
            unit = max_match.group(2) or ''
            if 'hour' in unit or 'hr' in unit:
                max_val *= 60
            return None, max_val
        
                # 3. Look for Min floors: "over 30", "at least 30", "more than 30"
        min_match = re.search(r'(?:over|min|more than|at least)\s*(\d+)\s*(min|hour|hr)?', query)
        if min_match:
            min_val = int(min_match.group(1))
            unit = min_match.group(2) or ''
            if 'hour' in unit or 'hr' in unit:
                min_val *= 60
            return min_val, None

        # 4. Fallback: If it just says "40 mins" without modifiers, assume it's a maximum.
        single_match = re.search(r'(\d+)\s*(min|hour|hr)', query)
        if single_match:
            max_val = int(single_match.group(1))
            if 'hour' in single_match.group(2) or 'hr' in single_match.group(2):
                max_val *= 60
            return None, max_val

        return None, None


    def _prepare_filters(self, llm_filters: AssessmentFilters, raw_query: str) -> Dict[str, Any]:
        db_filters = {}
        if llm_filters.remote_support and llm_filters.remote_support not in ["None", "null"]:
            db_filters["remote_support"] = llm_filters.remote_support
        if llm_filters.adaptive_support and llm_filters.adaptive_support not in ["None", "null"]:
            db_filters["adaptive_support"] = llm_filters.adaptive_support

        # Use Python regex on the raw text
        min_duration, max_duration = self._extract_time_from_query(raw_query)
        if min_duration is not None:
            db_filters["min_duration"] = min_duration
        if max_duration is not None:
            db_filters["max_duration"] = max_duration


        return db_filters

    def get_recommendations(self, raw_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        print(f"\n🚀 Processing Request: '{raw_query[:50]}...'")
        
        analysis = self.router.analyze(raw_query)
        search_query = analysis.search_query
        base_filters = self._prepare_filters(analysis.filters, raw_query)

        print(f"Prepared DB Filters: {base_filters}")
        
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

            # print("!!!!!!!!!!res:", res)
            
        return formatted_output