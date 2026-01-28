# ITSM Agent Container Management Script
# Usage: .\manage-containers.ps1 [start|stop|logs|rebuild|clean]

param(
    [string]$Action = "start",
    [switch]$Help
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommandPath
$ComposeFile = Join-Path $ProjectRoot "docker-compose.yml"

function Show-Help {
    Write-Host @"
ITSM Agent Container Manager

Usage: .\manage-containers.ps1 [action] [options]

Actions:
  start       Start all containers (default)
  stop        Stop all containers
  restart     Restart all containers
  logs        Show live logs from all services
  rebuild     Rebuild and start containers
  clean       Remove all containers and volumes
  status      Show container status
  shell       Open shell in backend container
  test        Test API connectivity

Examples:
  .\manage-containers.ps1 start
  .\manage-containers.ps1 logs
  .\manage-containers.ps1 stop
"@
}

function Test-Podman {
    try {
        $version = podman --version 2>&1
        Write-Host "✓ Podman found: $version" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ Podman not found. Please install from https://podman.io/docs/installation" -ForegroundColor Red
        return $false
    }
}

function Test-Compose {
    try {
        $version = podman-compose --version 2>&1
        Write-Host "✓ Podman-compose found: $version" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "! Podman-compose not found, but this may be okay on some systems" -ForegroundColor Yellow
        return $false
    }
}

function Start-Containers {
    Write-Host "Starting containers..." -ForegroundColor Cyan
    podman-compose -f $ComposeFile up -d --build
    
    Write-Host "`nWaiting for services to be healthy..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5
    
    Write-Host "`n✓ Services started!" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:8000" -ForegroundColor Green
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
    Write-Host "  Ollama: http://localhost:11434" -ForegroundColor Green
}

function Stop-Containers {
    Write-Host "Stopping containers..." -ForegroundColor Cyan
    podman-compose -f $ComposeFile down
    Write-Host "✓ Containers stopped" -ForegroundColor Green
}

function Restart-Containers {
    Write-Host "Restarting containers..." -ForegroundColor Cyan
    podman-compose -f $ComposeFile restart
    Write-Host "✓ Containers restarted" -ForegroundColor Green
}

function Show-Logs {
    Write-Host "Showing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    podman-compose -f $ComposeFile logs -f
}

function Rebuild-Containers {
    Write-Host "Rebuilding containers..." -ForegroundColor Cyan
    podman-compose -f $ComposeFile up -d --build --force-recreate
    Write-Host "✓ Containers rebuilt and started" -ForegroundColor Green
}

function Clean-Containers {
    Write-Host "This will remove all containers, images, and volumes. Are you sure? (y/n)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq 'y') {
        Write-Host "Cleaning up..." -ForegroundColor Cyan
        podman-compose -f $ComposeFile down -v
        podman system prune -f
        Write-Host "✓ Cleanup complete" -ForegroundColor Green
    }
    else {
        Write-Host "Cancelled" -ForegroundColor Yellow
    }
}

function Show-Status {
    Write-Host "Container Status:" -ForegroundColor Cyan
    podman-compose -f $ComposeFile ps
}

function Open-Shell {
    Write-Host "Opening shell in backend container..." -ForegroundColor Cyan
    podman-compose -f $ComposeFile exec backend /bin/bash
}

function Test-Api {
    Write-Host "Testing API connectivity..." -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Frontend is accessible" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "✗ Frontend not responding" -ForegroundColor Red
    }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -ErrorAction Stop
        Write-Host "✓ Ollama is accessible" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Ollama not responding (may still be starting)" -ForegroundColor Yellow
    }
}

# Main execution
if ($Help) {
    Show-Help
    exit 0
}

Write-Host "ITSM Agent Container Manager" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Check prerequisites
if (-not (Test-Podman)) {
    exit 1
}

# Route to action
switch ($Action.ToLower()) {
    "start" { Start-Containers }
    "stop" { Stop-Containers }
    "restart" { Restart-Containers }
    "logs" { Show-Logs }
    "rebuild" { Rebuild-Containers }
    "clean" { Clean-Containers }
    "status" { Show-Status }
    "shell" { Open-Shell }
    "test" { Test-Api }
    default { 
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
