# Deploy to Render via CLI

Two scripts to deploy all 3 services to Render programmatically:

## Prerequisites

1. **Render Account**: https://render.com (sign up)
2. **Render API Token**: Get from https://dashboard.render.com/account/api-tokens
3. **PowerShell** (Windows) or **Bash** (Linux/macOS)

---

## Option A: PowerShell (Windows)

```powershell
# Get your API token from https://dashboard.render.com/account/api-tokens

.\deploy-to-render.ps1 -ApiToken "YOUR_RENDER_API_TOKEN" -GitRepo "dheerajp1728/IntelliTrack_llm"
```

**Example:**
```powershell
.\deploy-to-render.ps1 -ApiToken "rnd_abc123xyz..." -GitRepo "dheerajp1728/IntelliTrack_llm"
```

---

## Option B: Bash (Linux/macOS)

```bash
# Make script executable
chmod +x deploy-to-render.sh

# Run with API token
./deploy-to-render.sh -t YOUR_RENDER_API_TOKEN -r dheerajp1728/IntelliTrack_llm
```

**Example:**
```bash
./deploy-to-render.sh -t "rnd_abc123xyz..." -r "dheerajp1728/IntelliTrack_llm"
```

---

## What Gets Deployed

| Service | Image | Port | Env Vars |
|---------|-------|------|----------|
| **Ollama** | `ollama/ollama:latest` | 11434 | `OLLAMA_HOST=0.0.0.0:11434` |
| **Qdrant** | `qdrant/qdrant:latest` | 6333 | (none) |
| **FastAPI** | `docker.io/deeru2001/intellitrack-llm:latest` | 8000 | URLs for Ollama & Qdrant |

---

## Monitor Deployment

After running the script:

1. Go to **https://dashboard.render.com**
2. Click **Services** in the left sidebar
3. You should see all 3 services deploying

Each service takes 2-5 minutes to start.

---

## Get Service URLs

Once deployed, each service gets a unique URL:

- **Ollama**: `https://intellitrack-ollama-xxxx.onrender.com:11434`
- **Qdrant**: `https://intellitrack-qdrant-xxxx.onrender.com:6333`
- **FastAPI**: `https://intellitrack-llm-xxxx.onrender.com`

Test the app:
```
https://intellitrack-llm-xxxx.onrender.com/docs
```

---

## Troubleshooting

**"Authorization failed"**
- Check your API token is correct
- Generate a new one at https://dashboard.render.com/account/api-tokens

**"Service creation failed"**
- Verify Docker Hub images are public
- Check network connectivity

**Services not starting**
- Check Render dashboard for error logs
- Ensure ports are correct (11434 for Ollama, 6333 for Qdrant, 8000 for FastAPI)
