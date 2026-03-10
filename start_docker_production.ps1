# Startup script for Zuberabot Production (Docker)
Write-Host "Starting Zuberabot Production Environment..." -ForegroundColor Green

# Ensure Docker is running
if (!(Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop does not seem to be running. Please start it first." -ForegroundColor Red
    exit 1
}

# Build and start containers
Write-Host "Building and starting containers..." -ForegroundColor Yellow
docker-compose up -d --build

# Check status
if ($?) {
    Write-Host "Zuberabot is running!" -ForegroundColor Green
    docker-compose ps
    Write-Host "`nLogs follow (Ctrl+C to exit logs, container keeps running):" -ForegroundColor Cyan
    docker-compose logs -f nanobot
}
else {
    Write-Host "Failed to start Zuberabot." -ForegroundColor Red
}
