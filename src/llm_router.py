import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
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
    requires_balance: bool = Field(description="True ONLY if the query asks for BOTH technical/hard skills AND behavioral/soft skills.")
    filters: AssessmentFilters = Field(description="Explicit constraints mentioned in the query.")

class QueryRouter:
    """Analyzes raw text queries using an LLM to extract search parameters."""
    
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        # 1. Initialize the standard LLM (No .with_structured_output layer)
        self.llm = ChatGroq(model=model_name, temperature=0)
        
        # 2. Initialize the Pydantic parser (This safely extracts JSON from raw text)
        self.parser = PydanticOutputParser(pydantic_object=QueryAnalysis)
        
        # 3. Inject the parser's strict format instructions into the prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent search router for an HR assessment recommendation engine. Analyze the user's job description or query and extract the core requirements.\n\n{format_instructions}"),
            ("human", "{query}")
        ])
        
        # 4. Chain them together: Prompt -> LLM -> Parser
        self.chain = self.prompt | self.llm | self.parser

    def analyze(self, query: str) -> QueryAnalysis:
        # Pass both the user query and the strict format instructions to the chain
        return self.chain.invoke({
            "query": query,
            "format_instructions": self.parser.get_format_instructions()
        })