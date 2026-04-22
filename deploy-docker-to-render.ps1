# Deploy Docker containers to Render using API
# Specifically for deploying pre-built Docker images from Docker Hub

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiToken
)

$ErrorActionPreference = "Stop"
$API_BASE = "https://api.render.com/v1"

# Headers
$headers = @{
    "Accept"        = "application/json"
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer $ApiToken"
}

function Deploy-DockerService {
    param(
        [string]$Name,
        [string]$ImageUrl,
        [int]$Port,
        [hashtable]$EnvVars
    )
    
    # Convert env vars to proper format
    $envArray = @()
    if ($EnvVars) {
        foreach ($key in $EnvVars.Keys) {
            $envArray += @{
                "key"   = $key
                "value" = $EnvVars[$key]
            }
        }
    }
    
    # Simplified payload for Docker deployment
    $payload = @{
        "name"      = $Name
        "type"      = "web_service"
        "image"     = @{
            "imageUrl" = $ImageUrl
        }
        "envVars"   = $envArray
        "port"      = $Port
    }
    
    $jsonBody = $payload | ConvertTo-Json -Depth 10
    
    Write-Host "Deploying: $Name" -ForegroundColor Cyan
    Write-Host "Image: $ImageUrl" -ForegroundColor Gray
    Write-Host "Port: $Port" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri "$API_BASE/services" `
            -Method POST `
            -Headers $headers `
            -Body $jsonBody `
            -TimeoutSec 30
        
        $service = $response.Content | ConvertFrom-Json
        Write-Host "SUCCESS: $($service.name)" -ForegroundColor Green
        Write-Host "Service ID: $($service.id)" -ForegroundColor Green
        Write-Host "Status: $($service.status)" -ForegroundColor Green
        
        return @{ id = $service.id; name = $service.name; url = $service.notificationEmail }
    }
    catch [System.Net.WebException] {
        $response = $_.Exception.Response
        if ($response) {
            $statusCode = $response.StatusCode
            $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            
            Write-Host "FAILED: $Name" -ForegroundColor Red
            Write-Host "Status Code: $statusCode" -ForegroundColor Yellow
            Write-Host "Response: $responseBody" -ForegroundColor Yellow
        } else {
            Write-Host "FAILED: $Name" -ForegroundColor Red
            Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        return $null
    }
    catch {
        Write-Host "FAILED: $Name" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Yellow
        return $null
    }
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Yellow
Write-Host "Deploying IntelliTrack to Render" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow
Write-Host ""

# Deploy Ollama
Write-Host "[1/3] Ollama Service" -ForegroundColor Magenta
$ollama = Deploy-DockerService `
    -Name "intellitrack-ollama" `
    -ImageUrl "ollama/ollama:latest" `
    -Port 11434 `
    -EnvVars @{ "OLLAMA_HOST" = "0.0.0.0:11434" }

Write-Host ""

# Deploy Qdrant
Write-Host "[2/3] Qdrant Service" -ForegroundColor Magenta
$qdrant = Deploy-DockerService `
    -Name "intellitrack-qdrant" `
    -ImageUrl "qdrant/qdrant:latest" `
    -Port 6333 `
    -EnvVars @{}

Write-Host ""

# Deploy FastAPI
Write-Host "[3/3] FastAPI Service" -ForegroundColor Magenta
$fastapi = Deploy-DockerService `
    -Name "intellitrack-llm" `
    -ImageUrl "docker.io/deeru2001/intellitrack-llm:latest" `
    -Port 8000 `
    -EnvVars @{
        "OLLAMA_URL"        = "https://intellitrack-ollama.onrender.com"
        "QDRANT_URL"        = "https://intellitrack-qdrant.onrender.com"
        "PYTHONUNBUFFERED"  = "1"
    }

Write-Host ""
Write-Host "=================================" -ForegroundColor Yellow
Write-Host "Deployment Summary" -ForegroundColor Yellow
Write-Host "=================================" -ForegroundColor Yellow

if ($ollama) {
    Write-Host "✅ Ollama: $($ollama.id)" -ForegroundColor Green
}
if ($qdrant) {
    Write-Host "✅ Qdrant: $($qdrant.id)" -ForegroundColor Green
}
if ($fastapi) {
    Write-Host "✅ FastAPI: $($fastapi.id)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Monitor: https://dashboard.render.com" -ForegroundColor Cyan
Write-Host ""
