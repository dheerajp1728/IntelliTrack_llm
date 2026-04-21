# IntelliTrack LLM Service - Render Deployment

This is the LLM (Large Language Model) microservice for IntelliTrack that handles AI-powered project analysis.

## Overview

The IntelliTrack LLM Service analyzes GitHub repositories to determine project progress and task completion status using:
- **Code Indexing**: Extracts and indexes repository code
- **Semantic Search**: Uses vector embeddings (Nomic) to find relevant code
- **LLM Analysis**: Uses LLama-2-7b-chat to interpret code and determine progress
- **Qdrant Database**: Stores and searches code embeddings

## Quick Start (Render Deployment)

### Prerequisites
- GitHub account
- Render.com account
- Repository: https://github.com/dheerajp1728/IntelliTrack_llm

### Deploy on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service"
3. Select the `IntelliTrack_llm` repository
4. Configure:
   - **Name**: `intellitrack-llm`
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`

5. Environment Variables (optional - defaults to local setup):
   - `LM_STUDIO_URL` - Default: `http://localhost:1234`
   - `QDRANT_URL` - Default: `http://localhost:6333`
   - `GITHUB_TOKEN` - Optional GitHub token

6. Click "Create Web Service"

**Note**: For Render deployment with external LM Studio or Qdrant services, ensure they are publicly accessible.

## Local Development

### Setup

```bash
# Clone repository
git clone https://github.com/dheerajp1728/IntelliTrack_llm.git
cd IntelliTrack_llm

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Start External Services

**1. Qdrant (Vector Database)**:
```bash
docker run -p 6333:6333 qdrant/qdrant
# Health check: curl http://localhost:6333/health
```

**2. LM Studio (Local LLM)**:
- Download LM Studio: https://lmstudio.ai/
- Open application
- Download a model (e.g., `llama-2-7b-chat`)
- Click "Start Server" (will run on `127.0.0.1:1234`)

### Run Service

```bash
uvicorn main:app --reload
```

Service will be available at: `http://localhost:8000`

### API Documentation

Visit: `http://localhost:8000/docs`

## API Endpoints

### Health Check
```bash
GET /health
```
Response: `{"status": "ok", "service": "IntelliTrack LLM Service"}`

### Root
```bash
GET /
```
Response: Service info and documentation URL

### Analyze Repository
```bash
POST /progress
Content-Type: application/json

{
  "repo_url": "https://github.com/user/repo.git",
  "github_token": "ghp_xxxxxxxxxxxx",  # Optional for private repos
  "tasks": "Setup database; Create API; Add tests"
}
```

Response:
```json
{
  "results": [
    {"task": "Setup database", "progress": "In progress (45% complete)"},
    {"task": "Create API", "progress": "Not started"},
    {"task": "Add tests", "progress": "Done"}
  ],
  "progress_percent": 45
}
```

## Configuration

### Environment Variables

Create `.env` file:
```bash
# LM Studio endpoint
LM_STUDIO_URL=http://localhost:1234

# Qdrant vector database
QDRANT_URL=http://localhost:6333

# GitHub token (optional - for private repos and higher rate limits)
GITHUB_TOKEN=your_github_token_here

# Server port
PORT=8000
```

## File Structure

```
.
├── main.py                 # FastAPI application
├── llm_analyzer.py         # LLM integration
├── qdrant_indexer.py       # Qdrant client wrapper
├── code_indexer.py         # Repository code fetching
├── repo_code_fetcher.py    # GitHub code parser
├── requirements.txt        # Python dependencies
├── render.yaml             # Render deployment config
└── README.md               # This file
```

## How It Works

### Step-by-Step Analysis Flow

1. **Verify Repository Access** - Check GitHub API access
2. **Initialize Qdrant** - Connect to vector database
3. **Fetch & Index Code** - Clone repo and create embeddings
4. **Parse Tasks** - Split task list by delimiters
5. **Search Code** - Find relevant code snippets for each task
6. **LLM Analysis** - Send code + tasks to LLM for analysis
7. **Format Results** - Return progress for each task

### Detailed Process

```
Repository URL
    ↓
GitHub API Access Check
    ↓
Clone Repository
    ↓
Extract Code Files
    ↓
Create Embeddings (Nomic)
    ↓
Store in Qdrant
    ↓
Parse Task List
    ↓
Semantic Search for Each Task
    ↓
Retrieve Code Context
    ↓
Send to LLM (Llama-2-7b-chat)
    ↓
Parse LLM Response
    ↓
Calculate Progress %
    ↓
Return Results
```

## Troubleshooting

### Qdrant Connection Error
```
Check if Qdrant is running:
curl http://localhost:6333/health
```

### LM Studio Connection Error
```
Verify LM Studio is running:
curl http://127.0.0.1:1234/v1/completions
```

### Slow Response
- LLM analysis takes 30-60 seconds
- Larger repositories take longer to index
- Initial index is cached in Qdrant

### GitHub API Rate Limit
- Add `GITHUB_TOKEN` environment variable
- Use Personal Access Token from GitHub settings

## Integration with IntelliTrack

This service is designed to work with IntelliTrack Backend:

```python
# IntelliTrack Backend calls:
POST https://intellitrack-llm.onrender.com/progress
{
  "repo_url": "...",
  "tasks": "..."
}
```

The backend (`llm_integration.py`) handles:
- Timeout management (5 minutes)
- Error handling
- Health checks
- Service availability fallback

## Requirements

See [requirements.txt](requirements.txt):
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `requests` - HTTP client
- `python-dotenv` - Environment variables
- `pydantic` - Data validation
- `qdrant-client` - Vector DB client
- `nomic` - Embedding model

## Performance Tips

1. **First Run**: Takes longer (indexing repository)
2. **Subsequent Runs**: Faster (using cached embeddings)
3. **Model Size**: Use smaller models for faster response
4. **Task Count**: More tasks = longer analysis time
5. **Repository Size**: Larger repos = longer indexing

## Deployment Monitoring

### Check Service Health
```bash
curl https://intellitrack-llm.onrender.com/health
```

### View Logs
- Render Dashboard → Select Service → Logs tab
- Real-time logs show analysis progress

### Performance Metrics
- Response time monitored in logs
- Database operations tracked

## Advanced Configuration

### Custom Model Selection

Edit `llm_analyzer.py`:
```python
# Change model
MODEL_NAME = "mistral-7b"  # or other GGML model
```

### Custom Embeddings

Edit `qdrant_indexer.py`:
```python
# Use different embedding model
model_name = "all-MiniLM-L6-v2"  # or other model
```

## Support & Documentation

- API Docs: `{service-url}/docs`
- GitHub Issues: Report bugs
- Local testing: Run `test_api.py`

## License

Same as IntelliTrack main project
