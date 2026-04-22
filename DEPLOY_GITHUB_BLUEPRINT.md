# Render Deployment via GitHub Integration (Recommended)

This method connects your GitHub repo to Render and deploys directly.

---

## Method 1: Deploy via render.yaml (Recommended)

Your repository already has `render.yaml` configured with all 3 services!

### Step 1: Connect GitHub to Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Blueprint"**
3. Click **"Connect a Repository"**
4. Authorize GitHub and select: `dheerajp1728/IntelliTrack_llm`
5. Click **"Connect"**

### Step 2: Deploy Services

1. Leave defaults and click **"Create New Services"**
2. Render will automatically:
   - Read `render.yaml`
   - Create 3 services (Ollama, Qdrant, FastAPI)
   - Deploy Docker images from Docker Hub
   - Set environment variables

### Step 3: Monitor

Go to Services dashboard and wait for all 3 to show **"Live"** (2-5 min each)

---

## Method 2: Manual Dashboard (If Blueprint doesn't work)

If you prefer manual setup:

### Deploy Ollama
```
Dashboard → + New → Web Service
Image URL: ollama/ollama:latest
Name: intellitrack-ollama
Region: Oregon
Port: 11434
Env: OLLAMA_HOST=0.0.0.0:11434
```

### Deploy Qdrant
```
Dashboard → + New → Web Service
Image URL: qdrant/qdrant:latest
Name: intellitrack-qdrant
Region: Oregon
Port: 6333
```

### Deploy FastAPI
```
Dashboard → + New → Web Service
Image URL: docker.io/deeru2001/intellitrack-llm:latest
Name: intellitrack-llm
Region: Oregon
Port: 8000
Health Check: /health
Environment:
  OLLAMA_URL=https://intellitrack-ollama-xxxx.onrender.com
  QDRANT_URL=https://intellitrack-qdrant-xxxx.onrender.com
  PYTHONUNBUFFERED=1
```

---

## Why API Deployment Failed

- Free tier accounts may have API restrictions
- Account needs proper team/workspace configuration
- Render API requires specific request structure

**GitHub/Blueprint method is more reliable and recommended.**

---

## Links

- Dashboard: https://dashboard.render.com
- Blueprint Docs: https://render.com/docs/deployment-environments
- GitHub Integration: https://render.com/docs/github
