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
            "isFile" = $false
        }
    }
    
    $body = @{
        "name"           = $Name
        "type"           = "web_service"
        "image"          = @{
            "imageUrl" = $Image
        }
        "envVars"        = $envVars
        "exposedPort"    = $Port
        "planId"         = "free"
        "region"         = "oregon"
        "notificationEmail" = "test@example.com"
    } | ConvertTo-Json -Depth 10
    
    Write-Host "Creating service: $Name" -ForegroundColor Cyan
    Write-Host "Image: $Image" -ForegroundColor Gray
    Write-Host "Port: $Port" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri "$API_BASE/services" -Method POST -Headers $headers -Body $body -ErrorAction Stop
        
        $service = $response.Content | ConvertFrom-Json
        Write-Host "SUCCESS: Created $($service.name) - ID: $($service.id)" -ForegroundColor Green
        return $service.id
    }
    catch [System.Net.WebException] {
        Write-Host "ERROR: Failed to create $Name" -ForegroundColor Red
        $response = $_.Exception.Response
        if ($response) {
            Write-Host "HTTP Status: $($response.StatusCode)" -ForegroundColor Yellow
            $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
            $error_content = $reader.ReadToEnd()
            Write-Host "Response: $error_content" -ForegroundColor Yellow
        } else {
            Write-Host "Exception: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        return $null
    }
    catch {
        Write-Host "ERROR: Failed to create $Name" -ForegroundColor Red
        Write-Host "Exception: $($_.Exception.Message)" -ForegroundColor Yellow
        return $null
    }
}

Write-Host ""
Write-Host "Deploying IntelliTrack to Render..." -ForegroundColor Yellow
Write-Host ""

# Service 1: Ollama
$ollamaEnv = @{
    "OLLAMA_HOST" = "0.0.0.0:11434"
}
$ollamaId = Create-Service -Name "intellitrack-ollama" -Image "ollama/ollama:latest" -Port 11434 -Env $ollamaEnv

# Service 2: Qdrant
$qdrantEnv = @{}
$qdrantId = Create-Service -Name "intellitrack-qdrant" -Image "qdrant/qdrant:latest" -Port 6333 -Env $qdrantEnv

# Service 3: FastAPI
$fastAPIEnv = @{
    "OLLAMA_URL"        = "http://intellitrack-ollama.onrender.com:11434"
    "QDRANT_URL"        = "http://intellitrack-qdrant.onrender.com:6333"
    "PYTHONUNBUFFERED"  = "1"
    "GITHUB_TOKEN"      = ""
}
$fastAPIId = Create-Service -Name "intellitrack-llm" -Image "docker.io/deeru2001/intellitrack-llm:latest" -Port 8000 -Env $fastAPIEnv

Write-Host ""
Write-Host "Deployment Summary:" -ForegroundColor Yellow
Write-Host ""

if ($ollamaId) { Write-Host "SUCCESS: Ollama Service ID: $ollamaId" }
if ($qdrantId) { Write-Host "SUCCESS: Qdrant Service ID: $qdrantId" }
if ($fastAPIId) { Write-Host "SUCCESS: FastAPI Service ID: $fastAPIId" }

Write-Host ""
Write-Host "Services are deploying. Monitor at https://dashboard.render.com" -ForegroundColor Cyan
Write-Host ""
