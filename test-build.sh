#!/bin/bash
# Test Docker build locally

echo "Testing Docker build locally..."
docker build -t unifi-documenter:test . 

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
    echo "Testing container health..."
    
    # Run health check
    docker run --rm --name test-health unifi-documenter:test python healthcheck.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Health check passed!"
    else
        echo "❌ Health check failed!"
    fi
    
    # Clean up test image
    docker rmi unifi-documenter:test
else
    echo "❌ Docker build failed!"
    exit 1
fi