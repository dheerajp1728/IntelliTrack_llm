@echo off
REM Local testing script for Windows - runs Ollama via Docker, LLM service locally

echo.
echo 🚀 Starting Local LLM Service Test...
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker not installed!
    echo    Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✅ Docker found
echo.

REM Start services
echo 📦 Starting Ollama + Qdrant...
docker compose up -d

echo.
echo ⏳ Waiting 15 seconds for services to start...
timeout /t 15 /nobreak

REM Check Ollama
echo.
echo 🔍 Checking Ollama at http://localhost:11434...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama is running!
) else (
    echo ❌ Ollama not responding
    echo    Checking docker logs...
    docker compose logs ollama
    pause
    exit /b 1
)

REM Check Qdrant
echo.
echo 🔍 Checking Qdrant at http://localhost:6333...
curl -s http://localhost:6333/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Qdrant is running!
) else (
    echo ❌ Qdrant not responding
    pause
    exit /b 1
)

REM Pull model
echo.
echo 🤖 Pulling llama-2-7b-chat model...
echo    (This takes ~5-10 minutes on first run - be patient!)
echo.
docker exec intellitrack_llm_ollama_1 ollama pull llama-2-7b-chat
if %errorlevel% neq 0 (
    echo ❌ Failed to pull model
    pause
    exit /b 1
)

echo ✅ Model downloaded!

REM Install dependencies
echo.
echo 📚 Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Start LLM service
echo.
echo 🚀 Starting LLM Service on port 8001...
echo    API Docs: http://localhost:8001/docs
echo.
set OLLAMA_URL=http://localhost:11434
set QDRANT_URL=http://localhost:6333
python -m uvicorn main:app --host 0.0.0.0 --port 8001

pause
