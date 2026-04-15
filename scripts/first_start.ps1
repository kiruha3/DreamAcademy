#Requires -RunAsAdministrator
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
Write-Host "  DreamDocs Academy — First Start" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# 1. Check Docker
if (-not (Test-Command "docker")) {
    Write-Host "`n❌ Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "   Please install Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
}

$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Docker daemon is not running." -ForegroundColor Red
    Write-Host "   Please start Docker Desktop."
    exit 1
}
Write-Host "`n✅ Docker is installed and running." -ForegroundColor Green

# 2. Check .env
$envFile = Join-Path $PSScriptRoot "..\.env"
$envExample = Join-Path $PSScriptRoot "..\.env.example"
if (-not (Test-Path $envFile)) {
    Write-Host "`n⚠️  .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item $envExample $envFile
    Write-Host "   Please edit $envFile and set your MOODLE_TOKEN after Moodle setup." -ForegroundColor Yellow
}

# 3. Start containers
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

Write-Host "`n🚀 Starting Docker Compose..." -ForegroundColor Cyan
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ docker compose up failed." -ForegroundColor Red
    exit 1
}

# 4. Wait for Moodle
Write-Host "`n⏳ Waiting for Moodle to become ready (this may take 2–3 minutes on first start)..." -ForegroundColor Cyan
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
    Write-Host "`n❌ Moodle did not become ready in time." -ForegroundColor Red
    Write-Host "   Check logs: docker compose logs moodle"
    exit 1
}

Write-Host "`n✅ Moodle is ready at http://localhost:8080" -ForegroundColor Green

# 5. Check backend
Start-Sleep -Seconds 2
try {
    $api = Invoke-RestMethod -Uri "http://localhost:8000/" -TimeoutSec 5
    Write-Host "✅ Backend API is ready at http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend API is not responding yet. It will start after you set MOODLE_TOKEN." -ForegroundColor Yellow
}

# 6. Print next steps
Write-Host "`n==============================================" -ForegroundColor Cyan
Write-Host "  Next Steps (Moodle Web Services Setup)" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host @"

1. Open Moodle in your browser:
   http://localhost:8080

2. Login with default admin credentials:
   Username: admin
   Password: AdminPass123!

3. Navigate to:
   Site administration → Server → Web services → Overview

4. Follow the steps:
   a) Enable web services
   b) Enable REST protocol
   c) Create a service named "DreamDocs Portal"
   d) Add these functions to the service:
      - core_user_create_users
      - core_user_get_users
      - core_course_get_courses
      - core_course_create_courses
      - core_course_update_courses
      - enrol_manual_enrol_users
   e) Create a token for the admin user in this service

5. Copy the token and paste it into .env:
   MOODLE_TOKEN=your_token_here

6. Restart the backend container:
   docker compose restart portal-backend

7. Create your first course automatically:
   python scripts/setup_moodle_course.py http://localhost:8080 your_token_here

8. Open the Vue frontend:
   cd portal/frontend
   npm run dev
   # Then open http://localhost:5173

"@

Write-Host "✨ First start preparation complete!" -ForegroundColor Green
