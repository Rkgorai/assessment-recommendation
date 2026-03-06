import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import json
from typing import List, Dict

load_dotenv()

class AssessmentFilters(BaseModel):
    remote_support: Optional[str] = Field(description="Strictly 'Yes', 'No', or null")
    adaptive_support: Optional[str] = Field(description="Strictly 'Yes', 'No', or null")

class QueryAnalysis(BaseModel):
    refined_query: str = Field(description="The summarized and refined query preserving essential keywords and key points.")
    min_duration: Optional[int] = Field(description="Minimum duration in minutes. Return null if not specified.")
    max_duration: Optional[int] = Field(description="Maximum duration in minutes. Return null if not specified.")
    requires_balance: bool = Field(description="True if query requires BOTH technical (hard skills) and behavioral (soft skills) assessments.")
    filters: AssessmentFilters = Field(description="Specific categorical constraints like remote or adaptive support.")

class QueryRouter:
    """Uses LLM to summarize queries, extract durations, and format JSON."""
    
    def __init__(self):
        # We use a low temperature (0.1) so the LLM acts analytically, not creatively
        # model_name = "llama-3.1-8b-instant" 
        model_name = "moonshotai/kimi-k2-instruct-0905"
        self.llm = ChatGroq(model=model_name, temperature=0.1)
        self.parser = JsonOutputParser(pydantic_object=QueryAnalysis)
        
        self.prompt = PromptTemplate(
            template="""You are an expert HR Assessment AI Routing Engine.
Your task is to analyze the user's natural language query or Job Description (JD) and extract structured JSON data.

### INSTRUCTIONS:
1. REFINED QUERY: Find the key points, summarize, and refine the query. You MUST preserve essential keywords (specific skills, roles, and personality traits).
2. DURATION EXTRACTION: Extract the minimum and maximum assessment time limits in MINUTES. 
   - Convert hours to minutes (e.g., "1 hour" = 60).
   - ONLY extract time if it explicitly refers to the length of the test or assessment.
   - CRITICAL STRICT RULE: You MUST IGNORE numbers related to company history ("40 years ago"), years of experience ("5 years experience"), or age.
   - BOUNDARY RULES:
     * If the text says "not more than X", "under X", "maximum X", "up to X", "in X", or just mentions a time limit like "a 40 minute test" or "completed in 40 minutes": set max_duration = X, min_duration = null.
     * If the text says "at least X", "over X", or "minimum X": set min_duration = X, max_duration = null.
     * If the text specifies an exact range ("30-40 mins"): set min_duration = 30, max_duration = 40.
     * If no explicit test duration is mentioned: set both to null.
3. DOMAIN BALANCE: Set requires_balance to true ONLY IF the query explicitly asks for BOTH hard/technical skills AND soft/behavioral skills.
4. FILTERS: Extract 'remote_support' or 'adaptive_support' if explicitly mentioned. Otherwise set to null.

Format Instructions:
{format_instructions}

User Query:
{query}
""",
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        self.chain = self.prompt | self.llm | self.parser

    def analyze(self, query: str) -> QueryAnalysis:
        try:
            result = self.chain.invoke({"query": query})
            return QueryAnalysis(**result)
        except Exception as e:
            print(f"❌ LLM Routing Error: {e}")
            # Safe fallback if the LLM fails
            return QueryAnalysis(
                refined_query=query, 
                min_duration=None, 
                max_duration=None, 
                requires_balance=False, 
                filters=AssessmentFilters(remote_support=None, adaptive_support=None)
            )



class RerankResult(BaseModel):
    selected_urls: List[str] = Field(description="List of the exact assessment URLs that best match the query, ordered from most relevant to least.")

class AssessmentReranker:
    """Acts as a judge to evaluate and rerank candidate assessments against a Job Description."""
    
    def __init__(self):
        # Temperature 0.0 for strict analytical judging
        # reranker_model = "meta-llama/llama-4-scout-17b-16e-instruct"
        reranker_model = "llama-3.1-8b-instant"
        # reranker_model = "qwen/qwen3-32b"
        self.llm = ChatGroq(model=reranker_model, temperature=0.0)
        self.parser = JsonOutputParser(pydantic_object=RerankResult)
        
        self.prompt = PromptTemplate(
            template="""You are an expert HR Assessment Judge. 
Your task is to read a user's Job Description (JD) and a list of candidate assessments, and select the best matches.

### User Query / JD:
{query}

### Candidate Assessments:
{candidates}

### INSTRUCTIONS:
1. Evaluate each candidate assessment against the skills and requirements in the User Query.
2. Select up to {top_k} assessments that are the absolute best semantic and technical matches.
3. Return a JSON object with a single key 'selected_urls' containing the list of URLs of your chosen assessments.

Format Instructions:
{format_instructions}
""",
            input_variables=["query", "candidates", "top_k"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )
        
        self.chain = self.prompt | self.llm | self.parser

    def rerank(self, query: str, candidates: List[Dict], top_k: int) -> List[str]:
        # We strip down the candidates to save LLM token costs and prevent confusion
        simplified_candidates = [
            {
                "url": c.get('url'), 
                "name": c.get('name'), 
                "category": c.get('test_types', ''),
                "description": c.get('description', '')[:300] # Truncate long descriptions
            } 
            for c in candidates
        ]
        
        try:
            print(f"⚖️ LLM Reranker is evaluating {len(candidates)} candidates...")
            result = self.chain.invoke({
                "query": query, 
                "candidates": json.dumps(simplified_candidates), 
                "top_k": top_k
            })
            return result.get('selected_urls', [])[:top_k]
        except Exception as e:
            print(f"❌ Reranking Error: {e}")
            # Fallback: If the LLM fails, just return the top_k from the original ChromaDB search
            return [c.get('url') for c in candidates[:top_k]]