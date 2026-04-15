<#
.SYNOPSIS
    First start script for DreamDocs Academy.
.DESCRIPTION
    Checks prerequisites, starts Docker Compose, waits for Moodle readiness,
    and prints next steps for manual Moodle Web Services setup.
#>

$ErrorActionPreference = "Stop"

function Test-Command($cmd) {
    return [bool](Get-Command -Name $cmd -ErrorAction SilentlyContinue)
}

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  DreamDocs Academy - First Start" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# 1. Check Docker
if (-not (Test-Command "docker")) {
    Write-Host "`nERROR: Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "   Please install Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
}

$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nERROR: Docker daemon is not running." -ForegroundColor Red
    Write-Host "   Please start Docker Desktop."
    exit 1
}
Write-Host "`nOK Docker is installed and running." -ForegroundColor Green

# 2. Check .env
$envFile = Join-Path $PSScriptRoot "..\.env"
$envExample = Join-Path $PSScriptRoot "..\.env.example"
if (-not (Test-Path $envFile)) {
    Write-Host "`nWARNING .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item $envExample $envFile
    Write-Host "   Please edit $envFile and set your MOODLE_TOKEN after Moodle setup." -ForegroundColor Yellow
}

# 3. Start containers
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

Write-Host "`nBuilding Moodle image..." -ForegroundColor Cyan
docker compose build moodle

Write-Host "`nStarting Docker Compose..." -ForegroundColor Cyan
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nERROR docker compose up failed." -ForegroundColor Red
    exit 1
}

# 4. Wait for Moodle
Write-Host "`nWaiting for Moodle to become ready (this may take 2-3 minutes on first start)..." -ForegroundColor Cyan
$maxAttempts = 60
$attempt = 0
$moodleReady = $false

while ($attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 5
    $attempt++
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $moodleReady = $true
            break
        }
    } catch {
        Write-Host "   Attempt $attempt / $maxAttempts ..." -ForegroundColor DarkGray
    }
}

if (-not $moodleReady) {
    Write-Host "`nERROR Moodle did not become ready in time." -ForegroundColor Red
    Write-Host "   Check logs: docker compose logs moodle"
    exit 1
}

Write-Host "`nOK Moodle is ready at http://localhost:8080" -ForegroundColor Green

# 5. Check backend
Start-Sleep -Seconds 2
try {
    $api = Invoke-RestMethod -Uri "http://localhost:8000/" -TimeoutSec 5
    Write-Host "OK Backend API is ready at http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "WARNING Backend API is not responding yet. It will start after you set MOODLE_TOKEN." -ForegroundColor Yellow
}

# 6. Print next steps
Write-Host "`n==============================================" -ForegroundColor Cyan
Write-Host "  Next Steps (Moodle Web Services Setup)" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open Moodle in your browser:"
Write-Host "   http://localhost:8080"
Write-Host ""
Write-Host "2. Login with default admin credentials:"
Write-Host "   Username: admin"
Write-Host "   Password: AdminPass123!"
Write-Host ""
Write-Host "3. Navigate to:"
Write-Host "   Site administration -> Server -> Web services -> Overview"
Write-Host ""
Write-Host "4. Follow the steps:"
Write-Host "   a) Enable web services"
Write-Host "   b) Enable REST protocol"
Write-Host "   c) Create a service named DreamDocs Portal"
Write-Host "   d) Add these functions to the service:"
Write-Host "      - core_user_create_users"
Write-Host "      - core_user_get_users"
Write-Host "      - core_course_get_courses"
Write-Host "      - core_course_create_courses"
Write-Host "      - core_course_update_courses"
Write-Host "      - enrol_manual_enrol_users"
Write-Host "   e) Create a token for the admin user in this service"
Write-Host ""
Write-Host "5. Copy the token and paste it into .env:"
Write-Host "   MOODLE_TOKEN=your_token_here"
Write-Host ""
Write-Host "6. Restart the backend container:"
Write-Host "   docker compose restart portal-backend"
Write-Host ""
Write-Host "7. Create your first course automatically:"
Write-Host "   python scripts/setup_moodle_course.py http://localhost:8080 your_token"
Write-Host ""
Write-Host "8. Open the Vue frontend:"
Write-Host "   cd portal/frontend"
Write-Host "   npm run dev"
Write-Host "   # Then open http://localhost:5173"
Write-Host ""
Write-Host "First start preparation complete!" -ForegroundColor Green
