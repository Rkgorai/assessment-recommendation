import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

# Ensure Python can find the 'src' module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embeddings import EmbeddingManager
from src.vector_store import VectorStore
from src.retriever import AssessmentRetriever
# 🚨 ADDED: Imported the AssessmentReranker
from src.llm_router import QueryRouter, AssessmentReranker 
from src.recommender import AssessmentRecommender

# Initialize the FastAPI app
app = FastAPI(
    title="SHL Assessment Recommendation API",
    description="Intelligently routes, retrieves, and reranks SHL assessments based on job descriptions.",
    version="1.0.0"
)

# 1. Initialize the AI components globally so they only load once when the server starts
print("🚀 Initializing AI Engine...")
try:
    embedding_manager = EmbeddingManager()
    vector_store = VectorStore(persist_directory="./database/chroma_db")
    retriever = AssessmentRetriever(vector_store, embedding_manager)
    
    # 🚨 ADDED: Initialize both the Router (Pre-processor) and Reranker (Post-processor)
    router = QueryRouter()
    reranker = AssessmentReranker()
    
    # 🚨 ADDED: Pass the reranker into the recommender orchestration
    recommender = AssessmentRecommender(router, retriever, reranker)
    
    print("✅ AI Engine ready to accept requests.")
except Exception as e:
    print(f"❌ Failed to load AI components: {e}")
    recommender = None

# 2. Define the exact JSON structure we expect from the user
class QueryRequest(BaseModel):
    query: str

# 3. Define Endpoint 1: Health Check (Required by Rubric)
@app.get("/health")
def health_check():
    """Simple status check to verify the API is running."""
    if recommender is None:
        raise HTTPException(status_code=500, detail="AI Engine failed to initialize.")
    return {"status": "healthy"}

# 4. Define Endpoint 2: Assessment Recommendation (Required by Rubric)
@app.post("/recommend", response_model=Dict[str, List[Dict[str, Any]]])
def get_recommendations(request: QueryRequest):
    """Accepts a job description or query and returns 10 recommended assessments."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
    
    if recommender is None:
        raise HTTPException(status_code=500, detail="AI Engine is offline.")
        
    try:
        recommendations = recommender.get_recommendations(request.query, top_k=10)
        return { "recommended_assignments": recommendations }
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Run the server
if __name__ == "__main__":
    print("🌐 Starting local server on http://127.0.0.1:8000")
    
    uvicorn.run("api:app", host="0.0.0.0", port=10000)