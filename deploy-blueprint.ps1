# Deploy Blueprint to Render
# Usage: ./deploy-blueprint.ps1 -ApiToken "YOUR_TOKEN" -GitRepo "dheerajp1728/IntelliTrack_llm"

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiToken,
    
    [string]$GitRepo = "dheerajp1728/IntelliTrack_llm",
    [string]$BlueprintName = "intellitrack-llm-services",
    [string]$BlueprintPath = "render.yaml"
)

$ErrorActionPreference = "Stop"
$API_BASE = "https://api.render.com/v1"

# Headers
$headers = @{
    "Accept"        = "application/json"
    "Content-Type"  = "application/json"
    "Authorization" = "Bearer $ApiToken"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Deploying Blueprint to Render" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Step 1: Get GitHub repo info
Write-Host "[1/2] Connecting to GitHub repository..." -ForegroundColor Cyan
Write-Host "Repository: $GitRepo" -ForegroundColor Gray
Write-Host "Blueprint: $BlueprintPath" -ForegroundColor Gray

# Step 2: Create Blueprint deployment
Write-Host ""
Write-Host "[2/2] Creating Blueprint deployment..." -ForegroundColor Cyan

$payload = @{
    "repo"           = "https://github.com/$GitRepo"
    "branch"         = "main"
    "rootDir"        = "."
    "blueprintPath"  = $BlueprintPath
    "notificationEmail" = ""
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-WebRequest -Uri "$API_BASE/blueprints" `
        -Method POST `
        -Headers $headers `
        -Body $payload `
        -TimeoutSec 30
    
    $blueprint = $response.Content | ConvertFrom-Json
    Write-Host "SUCCESS: Blueprint created!" -ForegroundColor Green
    Write-Host "Blueprint ID: $($blueprint.id)" -ForegroundColor Green
    Write-Host "Status: Deploying services..." -ForegroundColor Green
}
catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Note: Blueprint deployment via API has restrictions." -ForegroundColor Yellow
    Write-Host "Please use manual deployment on Render dashboard:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Go to: https://dashboard.render.com/blueprints" -ForegroundColor Yellow
    Write-Host "2. Click: 'New Blueprint'" -ForegroundColor Yellow
    Write-Host "3. Connect: $GitRepo" -ForegroundColor Yellow
    Write-Host "4. Blueprint Path: $BlueprintPath" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "Deployment Started" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Monitor progress: https://dashboard.render.com" -ForegroundColor Cyan
Write-Host "Services: intellitrack-ollama, intellitrack-qdrant, intellitrack-llm" -ForegroundColor Cyan
Write-Host ""
