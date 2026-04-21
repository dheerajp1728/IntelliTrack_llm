# Running LLM Service in Docker

## Local Development

### **1. Start Services**

```bash
cd IntelliTrack_llm

# Start Ollama + Qdrant locally
docker-compose up -d

# Verify they're running
curl http://localhost:11434/api/tags    # Ollama
curl http://localhost:6333/health       # Qdrant
```

### **2. Pull a Model**

```bash
# Pull llama-2-7b-chat model
docker exec -it intellitrack_llm_ollama_1 ollama pull llama-2-7b-chat

# Or use a faster model
docker exec -it intellitrack_llm_ollama_1 ollama pull mistral
```

### **3. Run LLM Service**

```bash
# Set environment variables
export OLLAMA_URL=http://localhost:11434
export QDRANT_URL=http://localhost:6333

# Install dependencies
pip install -r requirements.txt

# Run service
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### **4. Test It**

```bash
curl -X POST http://localhost:8001/progress \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/your-repo",
    "tasks": "Task 1\nTask 2"
  }'
```

---

## Cloud Deployment (Render)

### **1. Push Docker Image to Docker Hub**

```bash
# Build image
docker build -f Dockerfile.lmstudio -t your-username/intellitrack-lm:latest .

# Login to Docker Hub
docker login

# Push
docker push your-username/intellitrack-lm:latest
```

### **2. Deploy on Render**

1. Go to https://render.com/dashboard
2. Click **"New +"** → **"Web Service"**
3. Select **"Docker"** as runtime
4. Enter Docker image: `your-username/intellitrack-lm:latest`
5. Set environment variables:
   ```bash
   OLLAMA_URL=http://localhost:11434
   QDRANT_URL=https://3d48d514-...aws.cloud.qdrant.io
   QDRANT_API_KEY=your-key
   GITHUB_TOKEN=your-token
   ```
6. Deploy!

---

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama API endpoint |
| `LM_STUDIO_URL` | `http://127.0.0.1:1234` | LM Studio (if using instead) |
| `QDRANT_URL` | `http://localhost:6333` | Vector database |
| `QDRANT_API_KEY` | - | Required for Qdrant Cloud |
| `GITHUB_TOKEN` | - | Optional, for private repos |

---

## Available Models

You can pull any Ollama model:

```bash
ollama pull llama-2-7b-chat      # 3.8GB, good quality
ollama pull mistral              # 4.1GB, fast
ollama pull neural-chat          # 3.8GB, optimized
ollama pull dolphin-mixtral      # Larger, better
```

---

## Troubleshooting

### Ollama not responding
```bash
docker logs intellitrack_llm_ollama_1
```

### Out of memory
```bash
# Increase Docker memory limit
docker update --memory 8g intellitrack_llm_ollama_1
```

### Model not loaded
```bash
# Check loaded models
curl http://localhost:11434/api/tags

# Load specific model
docker exec intellitrack_llm_ollama_1 ollama pull mistral
```
