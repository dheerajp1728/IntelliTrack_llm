#!/bin/bash

# Deploy to Render using API
# Usage: ./deploy-to-render.sh -t YOUR_RENDER_API_TOKEN -r dheerajp1728/IntelliTrack_llm

API_TOKEN=""
GIT_REPO=""
GIT_BRANCH="main"

# Parse arguments
while getopts "t:r:b:" opt; do
  case $opt in
    t) API_TOKEN="$OPTARG" ;;
    r) GIT_REPO="$OPTARG" ;;
    b) GIT_BRANCH="$OPTARG" ;;
    *) echo "Usage: $0 -t API_TOKEN -r GIT_REPO [-b GIT_BRANCH]"; exit 1 ;;
  esac
done

if [ -z "$API_TOKEN" ] || [ -z "$GIT_REPO" ]; then
  echo "❌ Missing required arguments"
  echo "Usage: $0 -t YOUR_API_TOKEN -r GIT_REPO"
  exit 1
fi

API_BASE="https://api.render.com/v1"

create_service() {
  local name=$1
  local image=$2
  local port=$3
  local env_json=$4
  
  echo "🔧 Creating service: $name"
  echo "   Image: $image"
  echo "   Port: $port"
  
  local payload=$(cat <<EOF
{
  "name": "$name",
  "type": "web_service",
  "image": {
    "image_url": "$image"
  },
  "env_vars": $env_json,
  "exposed_port": $port,
  "plan_id": "free"
}
EOF
)
  
  response=$(curl -s -X POST "$API_BASE/services" \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN" \
    -d "$payload")
  
  service_id=$(echo "$response" | jq -r '.id // empty')
  
  if [ -n "$service_id" ]; then
    echo "✅ Created: $name (ID: $service_id)"
    echo "$service_id"
  else
    echo "❌ Failed to create $name"
    echo "$response" | jq .
    return 1
  fi
}

# ============================================================================
# Deploy Services
# ============================================================================

echo ""
echo "🚀 Deploying IntelliTrack to Render..."
echo ""

# Service 1: Ollama
OLLAMA_ENV='[{"key": "OLLAMA_HOST", "value": "0.0.0.0:11434"}]'
OLLAMA_ID=$(create_service "intellitrack-ollama" "ollama/ollama:latest" 11434 "$OLLAMA_ENV")

# Service 2: Qdrant
QDRANT_ENV='[]'
QDRANT_ID=$(create_service "intellitrack-qdrant" "qdrant/qdrant:latest" 6333 "$QDRANT_ENV")

# Service 3: FastAPI
FASTAPI_ENV='[
  {"key": "OLLAMA_URL", "value": "http://intellitrack-ollama.onrender.com:11434"},
  {"key": "QDRANT_URL", "value": "http://intellitrack-qdrant.onrender.com:6333"},
  {"key": "PYTHONUNBUFFERED", "value": "1"},
  {"key": "GITHUB_TOKEN", "value": ""}
]'
FASTAPI_ID=$(create_service "intellitrack-llm" "docker.io/deeru2001/intellitrack-llm:latest" 8000 "$FASTAPI_ENV")

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "📋 Deployment Summary:"
echo ""
[ -n "$OLLAMA_ID" ] && echo "✅ Ollama Service ID: $OLLAMA_ID"
[ -n "$QDRANT_ID" ] && echo "✅ Qdrant Service ID: $QDRANT_ID"
[ -n "$FASTAPI_ID" ] && echo "✅ FastAPI Service ID: $FASTAPI_ID"

echo ""
echo "⏳ Services are deploying. Monitor at https://dashboard.render.com"
echo ""
