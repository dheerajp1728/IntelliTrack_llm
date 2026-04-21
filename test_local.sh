#!/bin/bash
# Local testing script - runs Ollama via Docker, LLM service locally

echo "🚀 Starting Local LLM Service Test..."
echo ""

# Step 1: Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed!"
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker found"

# Step 2: Start services
echo ""
echo "📦 Starting Ollama + Qdrant..."
docker compose up -d

# Step 3: Wait for services
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check Ollama
echo ""
echo "🔍 Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama is running!"
else
    echo "❌ Ollama not responding - check docker logs"
    docker compose logs ollama
    exit 1
fi

# Check Qdrant
echo ""
echo "🔍 Checking Qdrant..."
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant is running!"
else
    echo "❌ Qdrant not responding"
    docker compose logs qdrant
    exit 1
fi

# Step 4: Pull a model
echo ""
echo "🤖 Pulling llama-2-7b-chat model (this takes ~5-10 min)..."
docker exec intellitrack_llm_ollama_1 ollama pull llama-2-7b-chat

# Step 5: Install Python dependencies
echo ""
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Step 6: Run LLM service
echo ""
echo "🚀 Starting LLM Service..."
export OLLAMA_URL=http://localhost:11434
export QDRANT_URL=http://localhost:6333
python -m uvicorn main:app --host 0.0.0.0 --port 8001

echo ""
echo "✅ LLM Service running at http://localhost:8001"
echo "📚 API Docs: http://localhost:8001/docs"
