import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional

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