#!/bin/bash
set -e

# Unifi Backup Container Entrypoint Script
# Handles container initialization, environment setup, and process management

# Default values
DEFAULT_TZ="UTC"
DEFAULT_BACKUP_SCHEDULE="daily"
DEFAULT_BACKUP_TIME="02:00"
DEFAULT_BACKUP_RETENTION_DAYS="30"
DEFAULT_BACKUP_DIRECTORY="/app/backups"
DEFAULT_LOG_LEVEL="INFO"
DEFAULT_HEALTH_CHECK_PORT="8080"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_debug() {
    if [[ "${LOG_LEVEL:-INFO}" == "DEBUG" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    fi
}

# Signal handlers for graceful shutdown
shutdown_handler() {
    log_info "Received shutdown signal, performing graceful shutdown..."
    
    # Kill background processes
    if [[ -n "$BACKUP_PID" ]]; then
        log_info "Stopping backup process (PID: $BACKUP_PID)"
        kill -TERM "$BACKUP_PID" 2>/dev/null || true
        wait "$BACKUP_PID" 2>/dev/null || true
    fi
    
    if [[ -n "$HEALTH_PID" ]]; then
        log_info "Stopping health check process (PID: $HEALTH_PID)"
        kill -TERM "$HEALTH_PID" 2>/dev/null || true
        wait "$HEALTH_PID" 2>/dev/null || true
    fi
    
    log_info "Graceful shutdown completed"
    exit 0
}

# Setup signal traps
trap shutdown_handler SIGTERM SIGINT

# Function to validate environment variables
validate_environment() {
    local errors=0
    
    log_info "Validating environment configuration..."
    
    # Check required variables
    if [[ -z "$UNIFI_HOST" ]]; then
        log_error "UNIFI_HOST environment variable is required"
        errors=$((errors + 1))
    fi
    
    if [[ -z "$UNIFI_USERNAME" ]]; then
        log_error "UNIFI_USERNAME environment variable is required"
        errors=$((errors + 1))
    fi
    
    if [[ -z "$UNIFI_PASSWORD" ]]; then
        log_error "UNIFI_PASSWORD environment variable is required"
        errors=$((errors + 1))
    fi
    
    # Validate backup schedule
    if [[ -n "$BACKUP_SCHEDULE" ]]; then
        if [[ "$BACKUP_SCHEDULE" != "daily" && "$BACKUP_SCHEDULE" != "weekly" && ! "$BACKUP_SCHEDULE" =~ ^cron: ]]; then
            log_error "BACKUP_SCHEDULE must be 'daily', 'weekly', or start with 'cron:'"
            errors=$((errors + 1))
        fi
    fi
    
    # Validate backup time format
    if [[ -n "$BACKUP_TIME" ]]; then
        if ! [[ "$BACKUP_TIME" =~ ^[0-2][0-9]:[0-5][0-9]$ ]]; then
            log_error "BACKUP_TIME must be in HH:MM format (24-hour)"
            errors=$((errors + 1))
        fi
    fi
    
    # Validate retention days
    if [[ -n "$BACKUP_RETENTION_DAYS" ]]; then
        if ! [[ "$BACKUP_RETENTION_DAYS" =~ ^[0-9]+$ ]] || [[ "$BACKUP_RETENTION_DAYS" -lt 1 ]]; then
            log_error "BACKUP_RETENTION_DAYS must be a positive integer"
            errors=$((errors + 1))
        fi
    fi
    
    if [[ $errors -gt 0 ]]; then
        log_error "Environment validation failed with $errors error(s)"
        return 1
    fi
    
    log_info "Environment validation successful"
    return 0
}

# Function to setup environment defaults
setup_environment() {
    log_info "Setting up environment defaults..."
    
    # Set timezone
    export TZ="${TZ:-$DEFAULT_TZ}"
    ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime
    echo "$TZ" > /etc/timezone
    log_info "Timezone set to: $TZ"
    
    # Set backup configuration
    export BACKUP_SCHEDULE="${BACKUP_SCHEDULE:-$DEFAULT_BACKUP_SCHEDULE}"
    export BACKUP_TIME="${BACKUP_TIME:-$DEFAULT_BACKUP_TIME}"
    export BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-$DEFAULT_BACKUP_RETENTION_DAYS}"
    export BACKUP_DIRECTORY="${BACKUP_DIRECTORY:-$DEFAULT_BACKUP_DIRECTORY}"
    export LOG_LEVEL="${LOG_LEVEL:-$DEFAULT_LOG_LEVEL}"
    export HEALTH_CHECK_PORT="${HEALTH_CHECK_PORT:-$DEFAULT_HEALTH_CHECK_PORT}"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIRECTORY"
    
    # Set permissions for backup directory
    chown -R app:app "$BACKUP_DIRECTORY"
    
    log_info "Environment setup completed"
    log_info "Configuration:"
    log_info "  - Unifi Host: $UNIFI_HOST"
    log_info "  - Backup Schedule: $BACKUP_SCHEDULE"
    log_info "  - Backup Time: $BACKUP_TIME"
    log_info "  - Backup Directory: $BACKUP_DIRECTORY"
    log_info "  - Retention Days: $BACKUP_RETENTION_DAYS"
    log_info "  - Log Level: $LOG_LEVEL"
    log_info "  - Timezone: $TZ"
}

# Function to test connectivity
test_connectivity() {
    log_info "Testing connectivity to Unifi controller..."
    
    # Test network connectivity
    if ! ping -c 1 -W 5 "$UNIFI_HOST" >/dev/null 2>&1; then
        log_warn "Ping test to $UNIFI_HOST failed, but this might be normal if ICMP is disabled"
    else
        log_info "Ping test to $UNIFI_HOST successful"
    fi
    
    # Test SSH port connectivity
    if command -v nc >/dev/null 2>&1; then
        if nc -z -w5 "$UNIFI_HOST" "${UNIFI_PORT:-22}" >/dev/null 2>&1; then
            log_info "SSH port ${UNIFI_PORT:-22} is accessible on $UNIFI_HOST"
        else
            log_warn "SSH port ${UNIFI_PORT:-22} is not accessible on $UNIFI_HOST"
        fi
    fi
    
    # Test SSH authentication
    log_info "Testing SSH authentication..."
    if python3 -c "
import sys
sys.path.append('/app')
from unifi_backup import UnifiBackupManager
config = {
    'unifi_host': '$UNIFI_HOST',
    'unifi_username': '$UNIFI_USERNAME', 
    'unifi_password': '$UNIFI_PASSWORD',
    'unifi_port': ${UNIFI_PORT:-22},
    'connection_timeout': 10
}
manager = UnifiBackupManager(config)
if manager.test_connection():
    print('SUCCESS')
else:
    print('FAILED')
"; then
        if [[ "$(python3 -c "
import sys
sys.path.append('/app')
from unifi_backup import UnifiBackupManager
config = {
    'unifi_host': '$UNIFI_HOST',
    'unifi_username': '$UNIFI_USERNAME', 
    'unifi_password': '$UNIFI_PASSWORD',
    'unifi_port': ${UNIFI_PORT:-22},
    'connection_timeout': 10
}
manager = UnifiBackupManager(config)
print('SUCCESS' if manager.test_connection() else 'FAILED')
")" == "SUCCESS" ]]; then
            log_info "SSH authentication test successful"
        else
            log_error "SSH authentication test failed"
            return 1
        fi
    else
        log_error "Failed to run SSH authentication test"
        return 1
    fi
}

# Function to start health check server
start_health_check() {
    log_info "Starting health check server on port $HEALTH_CHECK_PORT..."
    
    python3 -c "
import http.server
import socketserver
import json
import sys
import os
sys.path.append('/app')
from backup_script import BackupOrchestrator

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            try:
                orchestrator = BackupOrchestrator()
                status = orchestrator.health_check()
                self.send_response(200 if status['status'] == 'healthy' else 503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(status, indent=2).encode())
            except Exception as e:
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {'status': 'unhealthy', 'error': str(e)}
                self.wfile.write(json.dumps(error_response, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

with socketserver.TCPServer(('', $HEALTH_CHECK_PORT), HealthCheckHandler) as httpd:
    httpd.serve_forever()
" &
    
    HEALTH_PID=$!
    log_info "Health check server started (PID: $HEALTH_PID)"
}

# Function to run backup in different modes
run_backup() {
    local mode="$1"
    
    log_info "Starting backup script in $mode mode..."
    
    case "$mode" in
        "once")
            log_info "Running single backup operation..."
            python3 /app/backup_script.py once
            ;;
        "scheduled")
            log_info "Running in scheduled mode..."
            python3 /app/backup_script.py &
            BACKUP_PID=$!
            log_info "Backup scheduler started (PID: $BACKUP_PID)"
            ;;
        "test")
            log_info "Running connection test..."
            python3 /app/backup_script.py health
            ;;
        *)
            log_error "Unknown backup mode: $mode"
            return 1
            ;;
    esac
}

# Main execution
main() {
    log_info "Starting Unifi Backup Container..."
    log_info "Version: $(cat /app/VERSION 2>/dev/null || echo 'development')"
    
    # Validate environment
    if ! validate_environment; then
        log_error "Environment validation failed, exiting..."
        exit 1
    fi
    
    # Setup environment
    setup_environment
    
    # Determine run mode from command line arguments
    MODE="${1:-scheduled}"
    
    case "$MODE" in
        "once")
            log_info "Single backup mode requested"
            if test_connectivity; then
                run_backup "once"
            else
                log_error "Connectivity test failed, cannot run backup"
                exit 1
            fi
            ;;
        "test")
            log_info "Test mode requested"
            if test_connectivity; then
                run_backup "test"
            else
                exit 1
            fi
            ;;
        "scheduled"|*)
            log_info "Scheduled mode requested"
            
            # Test connectivity (non-blocking)
            test_connectivity || log_warn "Initial connectivity test failed, but continuing with scheduled mode..."
            
            # Start health check server
            start_health_check
            
            # Start backup scheduler
            run_backup "scheduled"
            
            # Wait for processes
            log_info "Container initialization complete, monitoring processes..."
            
            while true; do
                # Check if backup process is still running
                if [[ -n "$BACKUP_PID" ]] && ! kill -0 "$BACKUP_PID" 2>/dev/null; then
                    log_error "Backup process died unexpectedly, restarting..."
                    run_backup "scheduled"
                fi
                
                # Check if health check process is still running
                if [[ -n "$HEALTH_PID" ]] && ! kill -0 "$HEALTH_PID" 2>/dev/null; then
                    log_warn "Health check process died, restarting..."
                    start_health_check
                fi
                
                sleep 30
            done
            ;;
    esac
}

# Execute main function with all arguments
main "$@"