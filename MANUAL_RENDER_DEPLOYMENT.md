# Manual Render Deployment Guide

The automated API deployment script requires team setup. Here's how to deploy manually via Render Dashboard:

## Prerequisites
- Render Account: https://render.com
- API Token (already have): rnd_vkS6fUewyozydblkPg8cvaJIYXMe
- Docker images ready (built and pushed)

---

## Step 1: Deploy Ollama Service

1. Go to **https://dashboard.render.com**
2. Click **"+ New"** → **"Web Service"**
3. Click **"Deploy an existing image from a registry"**
4. Fill in:
   - **Image URL**: `ollama/ollama:latest`
   - **Name**: `intellitrack-ollama`
   - **Region**: `Oregon (US West)`
   - **Plan**: `Free`
   - **Port**: `11434`
5. Go to **"Advanced"** tab:
   - **Environment Variables**:
     - `OLLAMA_HOST=0.0.0.0:11434`
6. Click **"Create Web Service"**
7. **Copy the service URL** (e.g., `https://intellitrack-ollama-xxxx.onrender.com`)
8. Wait 2-5 minutes for deployment

---

## Step 2: Deploy Qdrant Service

1. Click **"+ New"** → **"Web Service"**
2. Click **"Deploy an existing image from a registry"**
3. Fill in:
   - **Image URL**: `qdrant/qdrant:latest`
   - **Name**: `intellitrack-qdrant`
   - **Region**: `Oregon (US West)`
   - **Plan**: `Free`
   - **Port**: `6333`
4. Click **"Create Web Service"**
5. **Copy the service URL** (e.g., `https://intellitrack-qdrant-xxxx.onrender.com`)
6. Wait 2-5 minutes for deployment

---

## Step 3: Deploy FastAPI Service

1. Click **"+ New"** → **"Web Service"**
2. Click **"Deploy an existing image from a registry"**
3. Fill in:
   - **Image URL**: `docker.io/deeru2001/intellitrack-llm:latest`
   - **Name**: `intellitrack-llm`
   - **Region**: `Oregon (US West)`
   - **Plan**: `Free`
   - **Port**: `8000`
4. Go to **"Advanced"** tab:
   - **Health Check Path**: `/health`
   - **Environment Variables**:
     ```
     OLLAMA_URL=https://intellitrack-ollama-xxxx.onrender.com
     QDRANT_URL=https://intellitrack-qdrant-xxxx.onrender.com
     PYTHONUNBUFFERED=1
     GITHUB_TOKEN=(leave blank or add your token)
     ```
     Replace `xxxx` with your actual service URLs from Steps 1 & 2
5. Click **"Create Web Service"**
6. Wait 2-5 minutes for deployment

---

## Step 4: Verify Deployment

1. Once all 3 services show **"Live"** on the dashboard
2. Go to FastAPI service URL: `https://intellitrack-llm-xxxx.onrender.com/docs`
3. You should see the Swagger UI with endpoints

---

## Service URLs

After deployment, you'll have:
- **Ollama**: `https://intellitrack-ollama-xxxx.onrender.com`
- **Qdrant**: `https://intellitrack-qdrant-xxxx.onrender.com`
- **FastAPI**: `https://intellitrack-llm-xxxx.onrender.com`

---

## Troubleshooting

**Service stuck in deploying**
- Check logs in Render dashboard: Click service → "Logs" tab
- Common issue: Docker image not found or too large

**Service crashes after deploy**
- Check logs: Click service → "Logs" tab
- Verify environment variables are correct
- Check health endpoint is responding

**Services can't communicate**
- Use full HTTPS URLs (not localhost)
- Example: `https://intellitrack-ollama-xxxx.onrender.com:11434`

**Free tier limitations**
- Services sleep after 15 minutes of inactivity
- First request will take 30 seconds to wake up
- Upgrade to paid plan for always-on deployment

---

## Dashboard Link

Monitor all services: https://dashboard.render.com/services
