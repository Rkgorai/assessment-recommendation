import json
import os
import sys

# Ensure Python can find the 'src' module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embeddings import EmbeddingManager
from src.vector_store import VectorStore
from src.retriever import AssessmentRetriever
from src.llm_router import QueryRouter
from src.recommender import AssessmentRecommender

def run_inference_loop():
    print("🚀 Booting up the SHL Recommendation Engine...")
    
    try:
        # 1. Initialize all modular components
        embedding_manager = EmbeddingManager()
        vector_store = VectorStore(persist_directory="./database/chroma_db")
        retriever = AssessmentRetriever(vector_store, embedding_manager)
        router = QueryRouter()
        recommender = AssessmentRecommender(router, retriever)
        
        print("\n✅ System Ready! Type 'exit' to stop.")
        print("-" * 60)
        
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return

    # 2. Start the interactive testing loop
    while True:
        user_query = input("\n📝 Enter JD or query (or 'exit'): ")
        
        if user_query.strip().lower() == 'exit':
            print("👋 Shutting down. Great work!")
            break
            
        if not user_query.strip():
            continue

        try:
            # 3. Pass the query to the orchestrator
            results = recommender.get_recommendations(user_query, top_k=5)

            print("!!! RESULTS FROM RECOMMENDER:", results)
            
            # 4. Print the output beautifully
            print("\n🏆 FINAL RECOMMENDATIONS:")
            print(json.dumps(results, indent=4))
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")

if __name__ == "__main__":
    run_inference_loop()