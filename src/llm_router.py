import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Optional

# Load keys safely
load_dotenv()

class AssessmentFilters(BaseModel):
    remote_support: Optional[str] = Field(default=None, description="'Yes' or 'No' only if explicitly requested.")
    adaptive_support: Optional[str] = Field(default=None, description="'Yes' or 'No' only if explicitly requested.")
    max_duration: Optional[str] = Field(default=None, description="Maximum test duration in minutes (e.g. '40').")

class QueryAnalysis(BaseModel):
    search_query: str = Field(description="The core semantic meaning of the job description or query.")
    filters: AssessmentFilters = Field(description="Explicit constraints mentioned in the query.")

class QueryRouter:
    """Analyzes raw text queries using an LLM to extract search parameters."""
    
    def __init__(self, model_name: str = "llama3-8b-8192"):
        self.llm = ChatGroq(model=model_name, temperature=0)
        self.structured_llm = self.llm.with_structured_output(QueryAnalysis)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent search router for an HR assessment recommendation engine. Analyze the user's job description or query and extract the core requirements."),
            ("human", "{query}")
        ])
        self.chain = self.prompt | self.structured_llm

    def analyze(self, query: str) -> QueryAnalysis:
        return self.chain.invoke({"query": query})