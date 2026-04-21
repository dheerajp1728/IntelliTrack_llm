# IntelliTrack LLM - Independent Microservice

This is a **separate, independent service** for AI-powered project analysis. Deploy this service separately from the main IntelliTrack application.

## Architecture

This LLM service is designed to be:
- ✅ **Independently deployed** on Render
- ✅ **Called remotely** by IntelliTrack Backend via HTTP
- ✅ **Scalable** - can be used by multiple applications
- ✅ **Decoupled** - separate repository, separate deployment

```
IntelliTrack Backend                IntelliTrack LLM Service
(intellitrack-backend.onrender.com) (intellitrack-llm.onrender.com)
         │                                    │
         │  POST /progress                    │
         │ (repo_url, tasks)                  │
         ├───────────────────────────────────>│
         │                                    │ Analyzes code
         │                                    │ Uses LLM
         │                                    │ Returns results
         │<───────────────────────────────────┤
         │  {results, progress_percent}       │
```

## Quick Deploy on Render

### Prerequisites
- GitHub account with this repository
- Render account (https://render.com)
- External LM Studio and Qdrant servers running

### Deploy Steps

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click**: "New" → "Web Service"
3. **Connect Repository**: Select this repository (IntelliTrack_llm)
4. **Configure**:
   - **Name**: `intellitrack-llm`
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
   - **Plan**: Free (minimum)

5. **Environment Variables**:
   - `PYTHONUNBUFFERED`: `1`
   - `LM_STUDIO_URL`: Your LM Studio server URL
   - `QDRANT_URL`: Your Qdrant server URL
   - `GITHUB_TOKEN`: (optional) GitHub token

6. **Deploy** and get your URL (e.g., `https://intellitrack-llm.onrender.com`)

7. **Use this URL** in IntelliTrack Backend's `LLM_SERVICE_URL` environment variable

---

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LM_STUDIO_URL` | LM Studio server URL | `http://your-server:1234` |
| `QDRANT_URL` | Qdrant database URL | `http://your-qdrant:6333` |
| `GITHUB_TOKEN` | GitHub API token (optional) | `ghp_xxxxx` |

### How to Get External Services

#### LM Studio (LLM Inference)
1. Download from https://lmstudio.ai/
2. Load a model (e.g., `llama-2-7b-chat`)
3. Start server on your machine/server
4. Get the URL (e.g., `http://192.168.1.100:1234`)

#### Qdrant (Vector Database)
```bash
# Option 1: Docker on your server
docker run -p 6333:6333 qdrant/qdrant

# Option 2: Qdrant Cloud
# Sign up at https://qdrant.tech/cloud/
```

---

## Local Development

### Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Start External Services

```bash
# Terminal 1: Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Terminal 2: LM Studio (open app and start server)

# Terminal 3: Start LLM service
uvicorn main:app --reload --port 8001
```

### Test

```bash
# Health check
curl http://localhost:8001/health

# Analyze repository
curl -X POST "http://localhost:8001/progress" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/dheerajp1728/IntelliTrack.git",
    "tasks": "Setup database; Create API; Add tests"
  }'
```

---

## API Endpoints

### Health Check
```
GET /health
```
Returns: `{"status": "ok", "service": "IntelliTrack LLM Service"}`

### Root
```
GET /
```
Returns: Service info and docs URL

### Analyze Repository
```
POST /progress
Content-Type: application/json

{
  "repo_url": "https://github.com/user/repo.git",
  "tasks": "Task 1; Task 2; Task 3",
  "github_token": "ghp_xxxx"  # optional
}
```

Response:
```json
{
  "results": [
    {"task": "Task 1", "progress": "In progress (60% complete)"},
    {"task": "Task 2", "progress": "Not started"},
    {"task": "Task 3", "progress": "Done"}
  ],
  "progress_percent": 53
}
```

---

## Integration with IntelliTrack Backend

After deploying this service, configure the backend:

1. **Copy deployed LLM service URL** (e.g., `https://intellitrack-llm.onrender.com`)
2. **Set in IntelliTrack Backend**:
   - Environment Variable: `LLM_SERVICE_URL`
   - Value: Your LLM service URL from step 1

3. **Backend endpoints** that use this service:
   - `GET /llm/health` - Check LLM service status
   - `POST /llm/analyze` - Analyze project progress

---

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application |
| `llm_analyzer.py` | LLM integration logic |
| `qdrant_indexer.py` | Vector database client |
| `code_indexer.py` | Repository code fetching |
| `repo_code_fetcher.py` | GitHub code parser |
| `requirements.txt` | Python dependencies |
| `render.yaml` | Render deployment config |

---

## Troubleshooting

### Service Returns 500 Error

Check logs in Render dashboard. Common causes:
- LM Studio server not running
- Qdrant database not accessible
- Incorrect environment variables

### LM Studio Connection Error

```
Error: Could not connect to LM Studio at http://xxx:1234
```

**Fix**:
1. Verify LM Studio is running and accessible
2. Check firewall settings
3. Verify `LM_STUDIO_URL` environment variable

### Qdrant Connection Error

```
Error: Could not connect to Qdrant at http://xxx:6333
```

**Fix**:
1. Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
2. Verify URL in environment variables
3. Check network connectivity

---

## Performance Tips

1. **First request is slow** - Repository indexing takes time
2. **Subsequent requests are faster** - Embeddings are cached in Qdrant
3. **LLM response time** - Depends on model size and complexity
4. **Timeout** - Set to 5 minutes for large repositories

---

## Important Notes

⚠️ **External Services Required**:
- This service requires LM Studio and Qdrant to be running
- These must be configured via environment variables
- Cannot run standalone on Render without these services

✅ **Best Practices**:
- Use managed Qdrant (Qdrant Cloud)
- Host LM Studio on a dedicated server or cloud instance
- Monitor service health regularly
- Set up alerts for downtime

---

## Support

- Documentation: See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md)
- Issues: Report on GitHub
- Integration: See IntelliTrack Backend `LLM_INTEGRATION_GUIDE.md`
