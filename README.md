# Assessment Recommendation Engine

Intelligent assessment recommendation engine using LLMs and vector embeddings. Implements multi-domain balancing (Hard vs. Soft skills) and modular data pipelines for scalable recruitment matching.

## Project Overview

This project includes a web scraper that extracts SHL product catalog data and processes assessment information. The data is stored in JSONL format for further analysis and recommendation.

---

## Prerequisites

- **Python 3.8 or higher**
- **pip** or **uv** (Python package managers)

---

## Installation

### 1. Create a Virtual Environment (Recommended)

```bash
# Using venv
python -m venv env

# Activate the virtual environment
# On Windows:
.\env\Scripts\activate
# On macOS/Linux:
source env/bin/activate
```

### 2. Install Dependencies

Install the required packages from `requirements.txt`:

```bash
# Using pip
pip install -r requirements.txt

# Or using uv
uv pip install -r requirements.txt
```

This will install:
- **scrapy** - Web scraping framework

---

## Running the Catalog Extractor

The spider extracts SHL assessment products from their product catalog.

### Command

```bash
cd scraper
scrapy runspider .\catalog_extractor.py
```

### What the Script Does

- **Scrapes SHL Product Catalog** (Type 1 & 2 assessments)
- **Extracts Product Information**:
  - Product name
  - Description
  - Duration (approximate completion time)
  - Test types (Ability & Aptitude, Competencies, etc.)
  - Remote support availability
  - Adaptive support availability
  - Product URL

- **Outputs Data**: Results are saved to `data/raw_catalog.jsonl` (one JSON object per line)

### Configuration

The spider includes these settings:
- **Concurrent Requests**: 16
- **Download Delay**: 0.25 seconds (to be respectful to the server)
- **User-Agent**: Chrome browser user agent

### Output

Each line in `data/raw_catalog.jsonl` contains a JSON object with:

```json
{
  "type": 1,
  "name": "Product Name",
  "url": "https://www.shl.com/products/...",
  "description": "Product description text",
  "duration": 30,
  "test_type": ["Ability & Aptitude", "Knowledge & Skills"],
  "adaptive_support": "Yes",
  "remote_support": "Yes"
}
```

---

## Directory Structure

```
assessment-recommendation/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── catalog_extractor.py               # Main spider script
├── data/
│   └── raw_catalog.jsonl             # Extracted catalog data (generated)
└── env/                               # Virtual environment
```

---

## Troubleshooting

### Issue: "scrapy: command not found"

**Solution**: Make sure the virtual environment is activated:
```bash
.\env\Scripts\activate  # Windows
source env/bin/activate # macOS/Linux
```

### Issue: "Module not found" errors

**Solution**: Reinstall dependencies:
```bash
pip install --upgrade -r requirements.txt
```

### Issue: Network/Timeout Errors

The script includes built-in delays and timeouts. If you experience connection issues:
- Check your internet connection
- The SHL website may be temporarily unavailable
- Try running the script again later

---

## Notes

- The spider respects server resources with a 0.25-second download delay
- Data is saved in JSONL format for efficient streaming and processing
- Type 1 assessments are processed first, followed by Type 2
- The script automatically creates the `data/` directory if it doesn't exist

---

## Next Steps

Once you have the catalog data, you can:
1. Process the JSONL file for data cleaning
2. Use LLMs to generate assessment recommendations
3. Build vector embeddings for semantic similarity matching
4. Implement the recommendation engine
