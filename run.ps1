# Build and run UniFi Documenter

# Build the Docker image
Write-Host "Building UniFi Documenter Docker image..." -ForegroundColor Green
docker build -t unifi-documenter .

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed successfully!" -ForegroundColor Green
    
    # Check if .env file exists
    if (-not (Test-Path ".env")) {
        Write-Host "Creating .env file from template..." -ForegroundColor Yellow
        Copy-Item ".env.template" ".env"
        Write-Host "Please edit .env file with your configuration before running!" -ForegroundColor Red
        return
    }
    
    Write-Host "Starting UniFi Documenter..." -ForegroundColor Green
    docker-compose up -d
    
    Write-Host "`nUniFi Documenter is now running!" -ForegroundColor Green
    Write-Host "Check logs with: docker-compose logs -f" -ForegroundColor Cyan
    Write-Host "Check status with: docker-compose ps" -ForegroundColor Cyan
    Write-Host "Stop with: docker-compose down" -ForegroundColor Cyan
    
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}