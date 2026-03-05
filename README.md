# 🎯 SHL Assessment Recommendation Engine

An intelligent, AI-powered system for recommending SHL assessments based on job descriptions. This project combines web scraping, semantic search (ChromaDB + embeddings), LLM routing (Groq/Llama 3), and a user-friendly Streamlit interface.

## 📋 Project Overview

The SHL Assessment Recommendation Engine automatically analyzes job descriptions and recommends the most appropriate SHL assessments. It leverages:

- **Web Scraping**: Extracts SHL product catalog data using Scrapy
- **Vector Database**: Stores embeddings in ChromaDB for semantic search
- **LLM Routing**: Uses Groq's Llama 3 to analyze requirements and balance technical/behavioral skills
- **FastAPI Backend**: RESTful API for programmatic access
- **Streamlit Frontend**: Interactive web UI for non-technical users

### Key Features

✅ **Smart Query Analysis**: Understands job descriptions and extracts requirements  
✅ **Multi-Domain Balancing**: Splits recommendations between technical and behavioral assessments  
✅ **Semantic Search**: Uses embeddings for accurate assessment matching  
✅ **Duration Filtering**: Respects time constraints (30 mins, 1-2 hours, etc.)  
✅ **Metadata Filtering**: Supports remote support, adaptive support filters  
✅ **Production-Ready**: FastAPI backend with health checks and error handling  

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│            Streamlit UI (app.py)                        │
│  - Natural language input                               │
│  - Beautiful result display                             │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP POST
┌──────────────────▼──────────────────────────────────────┐
│            FastAPI Backend (api.py)                     │
│  - /recommend endpoint                                  │
│  - /health endpoint                                     │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌──────────┐
    │LLM     │ │Vector  │ │Query     │
    │Router  │ │Store   │ │Analyzer  │
    │(Groq)  │ │(Chroma)│ │(Regex)   │
    └─┬──────┘ └─┬──────┘ └──────┬───┘
      │          │              │
      └──────────┴──────────────┘
            ▼
      ┌─────────────┐
      │  Raw Data   │
      │ (JSONL)     │
      └─────────────┘
```

---

## 📦 Prerequisites

- **Python 3.8+**
- **Groq API Key** (free tier available at https://console.groq.com)
- **Virtual Environment** (recommended)

---

## 🚀 Installation & Setup

### 1. Clone or Navigate to Project

```bash
cd assessment-recommendation
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv env
.\env\Scripts\activate

# macOS/Linux
python3 -m venv env
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get your free Groq API key from: https://console.groq.com

---

## 📂 Project Structure

```
assessment-recommendation/
├── api.py                           # FastAPI application
├── app.py                           # Streamlit UI
├── ingest_data.py                   # Data ingestion pipeline
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
│
├── src/
│   ├── __init__.py
│   ├── embeddings.py               # Embedding manager (sentence-transformers)
│   ├── llm_router.py               # LLM analysis (Groq/Llama 3)
│   ├── retriever.py                # Semantic search with filtering
│   ├── recommender.py              # Orchestration & result formatting
│   ├── vector_store.py             # ChromaDB wrapper
│   └── __pycache__/
│
├── scraper/
│   └── catalog_extractor.py        # Web scraper for SHL catalog
│
├── data/
│   └── raw_catalog.jsonl           # Extracted assessment data (generated)
│
├── database/
│   └── chroma_db/                  # ChromaDB vector database (generated)
│
├── notebooks/
│   └── main.ipynb                  # Exploration notebook
│
└── env/                            # Virtual environment
```

---

## 🔄 Workflow: Data Ingestion

### Step 1: Scrape SHL Catalog

```bash
cd scraper
scrapy runspider .\catalog_extractor.py
```

**Output**: `data/raw_catalog.jsonl`

Each line contains:
```json
{
  "name": "Assessment Name",
  "url": "https://www.shl.com/products/...",
  "description": "Description",
  "duration": 30,
  "test_type": ["Knowledge", "Ability"],
  "remote_support": "Yes",
  "adaptive_support": "No"
}
```

### Step 2: Ingest into Vector Database

```bash
python ingest_data.py
```

**What it does**:
- Loads JSONL data
- Generates embeddings using `sentence-transformers`
- Stores in ChromaDB for semantic search
- Batches operations for efficiency

**Output**: `database/chroma_db/` (persisted)

---

## 🎮 Running the Application

### Option A: Streamlit UI (Recommended for Users)

```bash
streamlit run app.py
```

Opens at: http://localhost:8501

**Features**:
- Natural language input ("I need a Java developer assessment")
- Beautiful table display with clickable links
- Real-time API communication

### Option B: FastAPI Backend Only

```bash
python api.py
```

Runs at: http://127.0.0.1:8000

**Endpoints**:

#### Health Check
```bash
GET /health
```

Response:
```json
{"status": "healthy"}
```

#### Get Recommendations
```bash
POST /recommend
Content-Type: application/json

{
  "query": "Java developers who can collaborate effectively. 40 minutes max."
}
```

Response:
```json
{
  "recommended_assignments": [
    {
      "name": "Assessment Name",
      "url": "https://...",
      "test_type": ["Knowledge", "Ability"],
      "duration": 30,
      "remote_support": "Yes",
      "adaptive_support": "No",
      "description": "..."
    }
  ]
}
```

#### Example cURL
```bash
curl -X POST http://127.0.0.1:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"query":"I need a quick Python assessment"}'
```

---

## 🧠 How It Works

### 1. Query Analysis (LLM Router)

When you submit: *"I need Java developers with soft skills, 30-40 minutes"*

The LLM extracts:
- **Search Query**: "Java developers soft skills"
- **Requires Balance**: ✓ (technical + behavioral)
- **Filters**: 
  - `min_duration`: 30 minutes
  - `max_duration`: 40 minutes

### 2. Balanced Retrieval

If balance is needed:
- Retrieves **technical assessments** (Knowledge-based)
- Retrieves **behavioral assessments** (Personality-based)
- Interleaves results for diversity

### 3. Post-Filtering

Python safeguards filter results by:
- Duration constraints
- Remote/adaptive support
- Test type categories

### 4. Formatting & Response

Results are formatted with:
- Assessment name & URL
- Type array
- Duration, support flags
- Description

---

## 🔧 Configuration

### Environment Variables (`.env`)

```env
# Required for LLM functionality
GROQ_API_KEY=your_api_key

# LLM Model (optional, defaults to llama-3.1-8b-instant)
GROQ_MODEL=llama-3.1-8b-instant
```

### Vector Store Settings (`src/vector_store.py`)

- **Persist Directory**: `./database/chroma_db/`
- **Collection Name**: `shl_assessments`
- **Embedding Model**: `all-MiniLM-L6-v2` (from sentence-transformers)

---

## 🧪 Testing

Run the test suite:

```bash
# Test API endpoints
python test_api.py

# Test inference pipeline
python test_inference.py
```

---

## 📊 Example Queries

```
"I'm hiring Java developers who need strong communication skills. Max 40 minutes."
→ Recommends mix of Knowledge + Personality assessments

"Backend engineer looking for adaptable candidates. Any assessment works."
→ Recommends top semantic matches

"Quick screening tool for teamwork. Under 20 minutes."
→ Filters by duration & retrieves behavioral assessments
```

---

## ⚠️ Troubleshooting

### Issue: "Module not found" (src.embeddings, etc.)

**Solution**: Ensure you're importing from project root:
```bash
cd assessment-recommendation
python api.py

```

### Issue: ChromaDB connection error

**Solution**: Rebuild the database:
```bash
rm -r database/chroma_db
python ingest_data.py
```

### Issue: GROQ_API_KEY not found

**Solution**: 
1. Create `.env` file in project root
2. Add your API key (get from https://console.groq.com)
3. Restart the app

### Issue: "Failed to connect to the backend"

**Solution**: Ensure FastAPI is running:
```bash
python api.py
# Should see: "🌐 Starting local server on http://127.0.0.1:8000"
```

### Issue: Slow embeddings generation

**Solution**: This is normal for first-time ingestion. The CPU-based embedding model (`all-MiniLM-L6-v2`) takes time. Subsequent queries use cached embeddings and are fast.

---

## 🛠️ Development Notes

### Key Components

| Module | Purpose |
|--------|---------|
| `embeddings.py` | Wraps sentence-transformers for embedding generation |
| `vector_store.py` | ChromaDB wrapper for persistence & querying |
| `retriever.py` | Semantic search + filtering |
| `llm_router.py` | Query analysis & filter extraction using Groq LLM |
| `recommender.py` | Orchestrates retrieval & formatting |

### Adding New Filters

To add a new filter (e.g., industry type):

1. **Update metadata** in `ingest_data.py`
2. **Update retriever** `where_clause` logic in `retriever.py`
3. **Update LLM prompt** in `llm_router.py` for extraction

---

For issues or questions:
- Check `.env` configuration
- Review console logs
- Test API directly with curl
- Verify ChromaDB was properly initialized

