#!/bin/bash
# Build and run UniFi Documenter

set -e

echo "Building UniFi Documenter Docker image..."
docker build -t unifi-documenter .

echo "Build completed successfully!"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "Please edit .env file with your configuration before running!"
    echo "Required settings: UDM_IP, UDM_ROOT_PASSWORD, AI_API_KEY"
    exit 1
fi

echo "Starting UniFi Documenter..."
docker-compose up -d

echo ""
echo "UniFi Documenter is now running!"
echo "Check logs with: docker-compose logs -f"
echo "Check status with: docker-compose ps"
echo "Stop with: docker-compose down"