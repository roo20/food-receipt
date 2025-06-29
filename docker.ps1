# Docker management script for Food Receipt Bot
param(
    [Parameter(Position=0)]
    [ValidateSet("help", "setup", "build", "up", "down", "restart", "logs", "shell", "test", "clean", "deploy", "status", "health")]
    [string]$Command = "help",
    
    [Parameter()]
    [ValidateSet("dev", "prod")]
    [string]$Env = "dev"
)

# Color output functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }

# Determine compose file
$ComposeFile = if ($Env -eq "prod") { "docker-compose.prod.yml" } else { "docker-compose.yml" }

function Show-Help {
    Write-Host "Food Receipt Bot - Docker Management Script" -ForegroundColor Green
    Write-Host ""
    Write-Host "Usage: .\docker.ps1 [command] [-Env dev|prod]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  help      Show this help message"
    Write-Host "  setup     Create .env file from template"
    Write-Host "  build     Build the Docker image"
    Write-Host "  up        Start the bot (detached)"
    Write-Host "  down      Stop and remove containers"
    Write-Host "  restart   Restart the bot"
    Write-Host "  logs      Show logs (follow)"
    Write-Host "  shell     Access container shell"
    Write-Host "  test      Run tests"
    Write-Host "  clean     Remove containers and images"
    Write-Host "  deploy    Full deployment (setup + build + up)"
    Write-Host "  status    Show container status"
    Write-Host "  health    Check container health"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\docker.ps1 setup"
    Write-Host "  .\docker.ps1 deploy"
    Write-Host "  .\docker.ps1 up -Env prod"
    Write-Host "  .\docker.ps1 logs"
}

function Setup-Environment {
    Write-Info "Setting up environment..."
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.template") {
            Copy-Item ".env.template" ".env"
            Write-Success "Created .env file from template"
            Write-Warning "Please edit .env file with your actual bot token and user ID"
            Write-Info "1. Get bot token from @BotFather on Telegram"
            Write-Info "2. Get your user ID from @userinfobot on Telegram"
        } else {
            Write-Error ".env.template file not found!"
            return $false
        }
    } else {
        Write-Info ".env file already exists"
    }
    return $true
}

function Build-Image {
    Write-Info "Building Docker image using $ComposeFile..."
    docker-compose -f $ComposeFile build
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Build completed successfully"
    } else {
        Write-Error "Build failed"
        return $false
    }
    return $true
}

function Start-Bot {
    Write-Info "Starting bot using $ComposeFile..."
    docker-compose -f $ComposeFile up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Bot started successfully"
        Write-Info "Use 'docker.ps1 logs' to view logs"
        Write-Info "Use 'docker.ps1 status' to check status"
    } else {
        Write-Error "Failed to start bot"
        return $false
    }
    return $true
}

function Stop-Bot {
    Write-Info "Stopping bot using $ComposeFile..."
    docker-compose -f $ComposeFile down
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Bot stopped successfully"
    } else {
        Write-Error "Failed to stop bot"
        return $false
    }
    return $true
}

function Restart-Bot {
    Write-Info "Restarting bot using $ComposeFile..."
    docker-compose -f $ComposeFile restart
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Bot restarted successfully"
    } else {
        Write-Error "Failed to restart bot"
        return $false
    }
    return $true
}

function Show-Logs {
    Write-Info "Showing logs from $ComposeFile..."
    docker-compose -f $ComposeFile logs -f telegram-bot
}

function Open-Shell {
    Write-Info "Opening shell in container..."
    docker-compose -f $ComposeFile exec telegram-bot bash
}

function Run-Tests {
    Write-Info "Running tests..."
    docker-compose -f $ComposeFile run --rm telegram-bot python test_receipt.py
}

function Clean-Up {
    Write-Warning "This will remove containers, networks, and images. Continue? (y/N)"
    $confirm = Read-Host
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        Write-Info "Cleaning up..."
        docker-compose -f $ComposeFile down --rmi all --volumes --remove-orphans
        Write-Success "Cleanup completed"
    } else {
        Write-Info "Cleanup cancelled"
    }
}

function Deploy-Bot {
    Write-Info "Starting full deployment..."
    if (-not (Setup-Environment)) { return $false }
    if (-not (Build-Image)) { return $false }
    if (-not (Start-Bot)) { return $false }
    Write-Success "Deployment completed successfully!"
    return $true
}

function Show-Status {
    Write-Info "Container status:"
    docker-compose -f $ComposeFile ps
}

function Check-Health {
    Write-Info "Checking container health..."
    docker-compose -f $ComposeFile ps
    
    $containerId = docker-compose -f $ComposeFile ps -q telegram-bot
    if ($containerId) {
        Write-Info "Health status:"
        $healthStatus = docker inspect --format='{{.State.Health.Status}}' $containerId 2>$null
        if ($healthStatus) {
            switch ($healthStatus) {
                "healthy" { Write-Success "Container is healthy" }
                "unhealthy" { Write-Error "Container is unhealthy" }
                "starting" { Write-Warning "Container health check is starting" }
                default { Write-Info "Health status: $healthStatus" }
            }
        } else {
            Write-Info "Health check not available"
        }
    }
}

# Check if Docker is available
try {
    docker --version | Out-Null
    docker-compose --version | Out-Null
} catch {
    Write-Error "Docker or Docker Compose not found. Please install Docker Desktop."
    exit 1
}

# Execute command
switch ($Command) {
    "help" { Show-Help }
    "setup" { Setup-Environment }
    "build" { Build-Image }
    "up" { Start-Bot }
    "down" { Stop-Bot }
    "restart" { Restart-Bot }
    "logs" { Show-Logs }
    "shell" { Open-Shell }
    "test" { Run-Tests }
    "clean" { Clean-Up }
    "deploy" { Deploy-Bot }
    "status" { Show-Status }
    "health" { Check-Health }
    default { 
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}
