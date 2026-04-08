# Agile Tracker - Project Progress Analysis System

A FastAPI-based service that analyzes project progress by analyzing repository code with an LLM to determine task completion status.

## Overview

Agile Tracker automatically:
1. Fetches code from GitHub repositories
2. Creates semantic embeddings of code using Nomic embeddings (768D vectors)
3. Stores embeddings in Qdrant vector database
4. Searches for relevant code matching your tasks
5. Uses LLM (LLama-2-7b-chat) to analyze implementation status
6. Returns structured progress analysis with a 0-100% completion score
ß
## Requirements

- **Python 3.8+** with virtual environment
- **Qdrant** vector database (Docker container on `localhost:6333`)
- **LM Studio** with a loaded model on `127.0.0.1:1234`
- **GitHub API** access (public repos don't need token, private repos require `github_token`)

## Quick Start (5 minutes)

### Step 1: Setup Python Environment

```bash
cd "Agile Tracker"
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# or: .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Step 2: Start Qdrant Vector Database

```bash
# Using Docker (recommended)
docker run -p 6333:6333 qdrant/qdrant

# Or: If you have Qdrant installed locally
qdrant --port 6333
```

Verify Qdrant is running: `curl http://localhost:6333/health`

### Step 3: Start LM Studio

1. **Open LM Studio** application on your machine
2. **Load a model** (e.g., `llama-2-7b-chat`)
3. **Click the server button** to start local inference
4. **Verify it's running**: `curl http://127.0.0.1:1234/v1/models`

### Step 4: Start the API Server

```bash
cd "Agile Tracker"
python -m uvicorn main:app --host 127.0.0.1 --port 8004
```

You'll see:
```
✅ Server started on http://127.0.0.1:8004
📊 Interactive docs at http://127.0.0.1:8004/docs
```

### Step 5: Test the API

```bash
curl -X POST "http://127.0.0.1:8004/progress" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/vignesh362/Search-Engine",
    "tasks": "Implement BM25\nBuild index\nCreate web interface"
  }'
```

Or run the comprehensive test suite:

```bash
python test_api.py
```

## API Usage

### Endpoint: POST /progress

Analyzes project progress for the given tasks.

**Request:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "github_token": "ghp_xxxx" |  null,    // Optional, for private repos
  "tasks": "Task 1\nTask 2\nTask 3"      // Newline-separated task list
}
```

**Response:**
```json
{
  "results": [
    {
      "task": "Implement BM25",
      "progress": "[done] - BM25 algorithm implemented in QueryProcessing.cpp"
    },
    {
      "task": "Build index",
      "progress": "[in progress] - Index building with VarByte compression in progress"
    },
    {
      "task": "Create web interface",
      "progress": "[not started] - No web interface code found in repository"
    }
  ],
  "progress_percent": 67
}
```

### Task Status Values

Each task will have one of these statuses:
- **`[done]`** - Feature is fully implemented and found in code
- **`[in progress]`** - Feature is partially implemented
- **`[not started]`** - No implementation found in code

## Example Usage

### Python

```python
import requests
import json

response = requests.post(
    "http://127.0.0.1:8004/progress",
    json={
        "repo_url": "https://github.com/vignesh362/Search-Engine",
        "tasks": "Implement BM25\nBuild index\nCreate web interface"
    }
)

data = response.json()

print(f"📈 Overall Progress: {data['progress_percent']}%")
print("\n📊 Task Status:")
for result in data['results']:
    print(f"  • {result['task']}")
    print(f"    └─ {result['progress']}")
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://127.0.0.1:8004/progress', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    repo_url: 'https://github.com/vignesh362/Search-Engine',
    tasks: 'Implement BM25\nBuild index\nCreate web interface'
  })
});

const data = await response.json();
console.log(`Progress: ${data.progress_percent}%`);
data.results.forEach(r => {
  console.log(`  ${r.task}: ${r.progress}`);
});
```

## Project Structure

```
Agile\ Tracker/
├── main.py                 # FastAPI application with /progress endpoint
├── qdrant_indexer.py       # Vector database client (Qdrant integration)
├── code_indexer.py         # Repository code fetching and embedding
├── llm_analyzer.py         # LLM-based progress analysis
├── repo_code_fetcher.py    # GitHub API interactions
├── test_api.py             # Comprehensive test suite
├── example_usage.py        # Usage patterns and examples
├── start.sh                # Automated startup script
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## How It Works

### Processing Pipeline

```
User Request
    ↓
[Step 1] Validate GitHub access
    ↓
[Step 2] Initialize Qdrant vector database
    ↓
[Step 3] Fetch repository code from GitHub
    ↓
[Step 4] Parse task list
    ↓
[Step 5] Generate embeddings & search for relevant code
    ↓
[Step 6] Send code + tasks to LLM for analysis
    ↓
[Step 7] Format and return results with progress %
    ↓
Response (0-100% + detailed task status)
```

### Timing

- **First request** (cold start): 45-60 seconds
  - 15-20s: GitHub fetch + embedding + Qdrant indexing
  - 30-40s: LLM analysis
- **Subsequent requests** (cached): 30-40 seconds
  - 1-2s: Code retrieval from Qdrant
  - 30-40s: LLM analysis

## Configuration

### Embedding Model

The system uses `text-embedding-nomic-embed-text-v1.5` which produces 768-dimensional vectors.

To use a different embedding model:
1. Update `code_indexer.py` line 35 (model name)
2. Update `qdrant_indexer.py` line 8 (vector_size parameter)
3. Restart server and delete existing Qdrant collections

### LLM Model

Default: `llama-2-7b-chat` (7B parameters, ~4GB VRAM)

To use a different model in LM Studio:
1. Load the model in LM Studio
2. No code changes needed - the API detects available models

For more capable analysis, try:
- `mistral-7b-instruct` (better reasoning)
- `neural-chat-7b` (optimized for chat)

### Timeout Adjustment

If you get timeout errors on large repositories, modify `llm_analyzer.py`:

```python
response = requests.post(self.api_url, json=payload, timeout=300)  # Change 300 to higher value
```

## Troubleshooting

### ❌ "Connection refused" on Qdrant

**Problem:** `[Errno 61] Connection refused`

**Solution:**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# If not running, start it:
docker run -p 6333:6333 qdrant/qdrant
```

### ❌ "Cannot connect to LLM"

**Problem:** LLM analysis times out or fails

**Solution:**
1. Verify LM Studio is running on `127.0.0.1:1234`
2. Check that a model is loaded and ready
3. Check system has enough memory (7GB+ for llama-2-7b)

### ❌ "Cannot access repository"

**Problem:** GitHub API returns 404 or access denied

**Solution:**
- For **public repos**: No token needed
- For **private repos**: Pass `github_token` parameter
- For **rate limiting**: Add a GitHub token to increase limits

### ❌ Vector dimension error (Fixed)

**Status:** ✅ **Already fixed in this version**

The system correctly uses 768-dimensional vectors matching the Nomic embedding model.

## Performance Tips

1. **Reuse collections**: Don't delete Qdrant collections between requests - results are cached
2. **Optimize task descriptions**: Be specific - generic tasks get less accurate results
3. **Batch requests**: Process multiple repos efficiently
4. **Monitor LM Studio**: Watch VRAM usage during analysis - slow LLM indicates memory pressure

## Testing

### Run the Full Test Suite

```bash
python test_api.py
```

This verifies:
- ✅ All three services are running
- ✅ API connectivity and response structure
- ✅ Sample analysis on a real repository
- ✅ JSON response format correctness

### Interactive API Documentation

Open in your browser: `http://127.0.0.1:8004/docs`

This provides:
- Live API endpoint testing
- Request/response schema documentation
- Try-it-out functionality

## Development & Debugging

### Enable Detailed Logging

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8004 --log-level debug
```

### Check Server Logs

The FastAPI server prints detailed progress to stdout:
```
======================================================================
📊 PROGRESS ANALYSIS REQUEST STARTED
======================================================================
Repository: https://github.com/vignesh362/Search-Engine
GitHub Token: No

[STEP 1/7] 🔍 Checking GitHub repository access...
✅ Repository access verified

[STEP 2/7] 🗄️  Initializing Qdrant vector database...
✅ Qdrant initialized

[STEP 3/7] 📥 Fetching and indexing repository code...
...
```

### Debug a Specific Component

```python
# Test Qdrant directly
from qdrant_indexer import QdrantIndexer
qdrant = QdrantIndexer()
print(qdrant.client.get_collections())

# Test code indexing
from code_indexer import sync_repo_to_qdrant
sync_repo_to_qdrant("https://github.com/vignesh362/Search-Engine", None, qdrant)

# Test LLM analysis
from llm_analyzer import LLMAnalyzer
llm = LLMAnalyzer()
code_samples = ["def foo(): pass"]
tasks = ["Create a function"]
results, percent = llm.analyze_tasks_with_summary(code_samples, tasks)
print(results, percent)
```

## Fixed Issues

This version includes fixes for:

✅ **Vector Dimension Mismatch** - Corrected to 768D vectors  
✅ **Deprecated Qdrant API** - Migrated to `query_points()`  
✅ **Response Validation** - Added missing `progress_percent` field  
✅ **LLM Timeout** - Increased from 30s to 300s (5 minutes)  
✅ **LLM Context Overflow** - Reduced prompt from 20K to 6K chars  
✅ **Silent Fallback Failures** - Replaced with explicit error handling  
✅ **Progress Visibility** - Added 7-step logging with timing breakdown  

## Architecture Diagram

```
┌──────────────────────────────────────────┐
│         Your Application/Client           │
└────────────────┬─────────────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │   FastAPI Server    │
        │  (main.py port 8004)│
        └────────┬────────────┘
                 │
      ┌──────────┼──────────┐
      │          │          │
      ▼          ▼          ▼
  ┌────────┐ ┌────────┐ ┌──────────┐
  │ GitHub │ │ Qdrant │ │LM Studio │
  │  API   │ │Vector  │ │ (LLama)  │
  │        │ │  DB    │ │          │
  └────────┘ └────────┘ └──────────┘
      │          │          │
      └──────────┼──────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │  Analysis Results   │
        │  (Task Status +%)   │
        └─────────────────────┘
```

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 8 GB | 16+ GB |
| Disk | 2 GB | 10+ GB (for repos) |
| Network | 1 Mbps | 10+ Mbps |

## License

This project integrates:
- **FastAPI** - Modern Python web framework
- **Qdrant** - Vector search database
- **LM Studio** - Local LLM inference
- **Nomic AI** - Embedding models
- **Python requests** - HTTP library

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review server logs for detailed error messages
3. Run `test_api.py` to diagnose service connectivity
4. Check that all three services (GitHub API, Qdrant, LM Studio) are accessible

## Changelog

**v1.0 (April 7, 2026)**
- ✅ Initial stable release
- ✅ All critical bugs fixed
- ✅ Comprehensive documentation
- ✅ Full test suite included
- ✅ Production-ready

---

**Last Updated:** April 7, 2026  
**Status:** ✅ Fully Functional & Tested
