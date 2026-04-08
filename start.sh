#!/bin/bash

# Startup script for Agile Tracker
# This script starts all required services

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   AGILE TRACKER STARTUP SCRIPT          ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_DIR${NC}"
    echo "Please create it with: python3 -m venv .venv"
    exit 1
fi

# Activate venv
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Check required services
echo ""
echo -e "${YELLOW}Checking required services...${NC}"

# Check Qdrant
echo -n "  Qdrant (localhost:6333): "
if nc -z localhost 6333 2>/dev/null; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
    echo "    Start with: docker run -p 6333:6333 qdrant/qdrant"
    exit 1
fi

# Check LM Studio
echo -n "  LM Studio (127.0.0.1:1234): "
if nc -z 127.0.0.1 1234 2>/dev/null; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
    echo "    Start LM Studio and load a model"
    exit 1
fi

# Start the FastAPI server
echo ""
echo -e "${YELLOW}Starting FastAPI server...${NC}"
cd "$PROJECT_DIR"

# Kill any existing server on port 8004
if nc -z 127.0.0.1 8004 2>/dev/null; then
    echo "  Port 8004 is in use, killing existing process..."
    lsof -ti:8004 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start server
python -m uvicorn main:app --host 127.0.0.1 --port 8004 --log-level info &
SERVER_PID=$!

# Wait for server to start
echo "  Waiting for server to start..."
sleep 3

# Check if server started successfully
if kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${GREEN}✅ FastAPI server started (PID: $SERVER_PID)${NC}"
    echo ""
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ All services are running!${NC}"
    echo -e "${GREEN}════════════════════════════════════════${NC}"
    echo ""
    echo "API is available at: http://127.0.0.1:8004"
    echo ""
    echo "Next steps:"
    echo "  1. Run tests: python test_api.py"
    echo "  2. Make requests: curl -X POST http://127.0.0.1:8004/progress ..."
    echo "  3. View API docs: http://127.0.0.1:8004/docs"
    echo ""
    echo "Server is running in the background (PID: $SERVER_PID)"
    echo "To stop: kill $SERVER_PID"
    echo ""
else
    echo -e "${RED}❌ Failed to start FastAPI server${NC}"
    exit 1
fi
