#!/bin/bash
set -e

# Create output and config directories with proper permissions
mkdir -p /app/output /app/config
chown -R unifi-user:unifi-user /app/output /app/config

# Switch to non-root user and run the application
exec gosu unifi-user python src/main.py