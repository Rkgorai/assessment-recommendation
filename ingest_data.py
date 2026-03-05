import json
import os
import sys

# Ensure Python can find the 'src' module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.embeddings import EmbeddingManager
from src.vector_store import VectorStore

def ingest_data():
    print("🚀 Starting Data Ingestion Pipeline...")
    
    # 1. Initialize DB and Embedding Components
    try:
        embedding_manager = EmbeddingManager()
        vector_store = VectorStore(persist_directory="./database/chroma_db")
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return

    # 2. Load the scraped data
    file_path = 'data/raw_catalog.jsonl'
    if not os.path.exists(file_path):
        print(f"❌ Error: Could not find {file_path}. Please make sure your scraped data is there.")
        return

    documents = []
    metadatas = []
    ids = []

    print(f"📂 Loading data from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # Safely handle the test_type list
            test_types_list = item.get("test_type", [])
            test_types_str = ", ".join(test_types_list) if isinstance(test_types_list, list) else ""
            
            # Force duration to be a strict integer for ChromaDB math filtering
            try:
                duration_val = int(item.get("duration", 0))
            except (ValueError, TypeError):
                duration_val = 0

            # --- THE RICH TEXT (For Semantic Search) ---
            rich_text = f"Assessment Name: {item.get('name', 'Unknown')}\nCategory: {test_types_str}\nDescription: {item.get('description', '')}"
            
            # --- THE METADATA (For Hard LLM Filtering) ---
            metadata = {
                "name": str(item.get("name", "Unknown")),
                "url": str(item.get("url", "")),
                "test_types": test_types_str,
                "duration": duration_val,
                "remote_support": str(item.get("remote_support", "No")).strip(),
                "adaptive_support": str(item.get("adaptive_support", "No")).strip()
            }
            
            documents.append(rich_text)
            metadatas.append(metadata)
            ids.append(f"shl_test_{idx}")

    if not documents:
        print("⚠️ No data found to ingest.")
        return

    # 3. Generate Embeddings and Batch Upsert into ChromaDB
    batch_size = 100
    print(f"\n🚀 Embedding and ingesting {len(documents)} assessments into ChromaDB in batches of {batch_size}...")

    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        print(f"   -> Processing batch {i} to {min(i+batch_size, len(documents))}...")
        
        # Call the modular embedding manager
        batch_embeddings = embedding_manager.generate_embeddings(batch_docs)
        
        # Call the modular vector store
        vector_store.add_assessments(batch_docs, batch_metas, batch_ids, batch_embeddings)

    print("\n🎉 Data ingestion complete! Your vector database is fully populated and ready.")

if __name__ == "__main__":
    ingest_data()