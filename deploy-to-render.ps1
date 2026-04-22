# Deploy to Render using API
# Usage: ./deploy-to-render.ps1 -ApiToken "YOUR_RENDER_API_TOKEN" -GitRepo "dheerajp1728/IntelliTrack_llm"

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiToken,
    
    [Parameter(Mandatory=$true)]
    [string]$GitRepo,
    
    [string]$GitBranch = "main"
)

$ErrorActionPreference = "Stop"

# Render API base URL
$API_BASE = "https://api.render.com/v1"

# Headers for API requests
$headers = @{
    "Accept"        = "application/json"
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer $ApiToken"
}

function Create-Service {
    param(
        [string]$Name,
        [string]$Image,
        [int]$Port,
        [hashtable]$Env
    )
    
    $envVars = @()
    foreach ($key in $Env.Keys) {
        $envVars += @{
            "key"   = $key
            "value" = $Env[$key]
        }
    }
    
    $body = @{
        "name"          = $Name
        "type"          = "web_service"
        "image"         = @{
            "image_url" = $Image
        }
        "env_vars"      = $envVars
        "exposed_port"  = $Port
        "plan_id"       = "free"
    } | ConvertTo-Json -Depth 10
    
    Write-Host "Creating service: $Name" -ForegroundColor Cyan
    Write-Host "Image: $Image" -ForegroundColor Gray
    Write-Host "Port: $Port" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri "$API_BASE/services" `
            -Method POST `
            -Headers $headers `
            -Body $body -ErrorAction Stop
        
        $service = $response.Content | ConvertFrom-Json
        Write-Host "✅ Created: $($service.name) - ID: $($service.id)" -ForegroundColor Green
        return $service.id
    }
    catch {
        Write-Host "❌ Failed to create $Name" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Yellow
        return $null
    }
}

# ============================================================================
# DEPLOY SERVICES
# ============================================================================

Write-Host "`n🚀 Deploying IntelliTrack to Render...`n" -ForegroundColor Yellow

# Service 1: Ollama
$ollamaEnv = @{
    "OLLAMA_HOST" = "0.0.0.0:11434"
}
$ollamaId = Create-Service -Name "intellitrack-ollama" -Image "ollama/ollama:latest" -Port 11434 -Env $ollamaEnv

# Service 2: Qdrant
$qdrantEnv = @{}
$qdrantId = Create-Service -Name "intellitrack-qdrant" -Image "qdrant/qdrant:latest" -Port 6333 -Env $qdrantEnv

# Service 3: FastAPI
# Note: You'll need to update these URLs once services are deployed
$fastAPIEnv = @{
    "OLLAMA_URL"        = "http://intellitrack-ollama.onrender.com:11434"
    "QDRANT_URL"        = "http://intellitrack-qdrant.onrender.com:6333"
    "PYTHONUNBUFFERED"  = "1"
    "GITHUB_TOKEN"      = ""
}
$fastAPIId = Create-Service -Name "intellitrack-llm" -Image "docker.io/deeru2001/intellitrack-llm:latest" -Port 8000 -Env $fastAPIEnv

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host "`n📋 Deployment Summary:`n" -ForegroundColor Yellow

if ($ollamaId) { Write-Host "✅ Ollama Service ID: $ollamaId" }
if ($qdrantId) { Write-Host "✅ Qdrant Service ID: $qdrantId" }
if ($fastAPIId) { Write-Host "✅ FastAPI Service ID: $fastAPIId" }

Write-Host "`n⏳ Services are deploying. Monitor at https://dashboard.render.com`n" -ForegroundColor Cyan
