#!/bin/bash
# Development and testing script for UniFi Documenter

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to display usage
usage() {
    echo "UniFi Documenter Development Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  install     - Install Python dependencies"
    echo "  test        - Run basic tests and validation"
    echo "  build       - Build Docker image"
    echo "  run         - Run the application locally"
    echo "  docker      - Run the Docker container"
    echo "  health      - Check application health"
    echo "  clean       - Clean build artifacts"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 install"
    echo "  $0 test"
    echo "  $0 build"
    echo "  $0 run --health"
    echo "  $0 docker --help"
}

# Install dependencies
install_deps() {
    log_info "Installing Python dependencies..."
    cd "$PROJECT_DIR"
    
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
    elif command -v pip &> /dev/null; then
        pip install -r requirements.txt
    else
        log_error "pip not found. Please install Python and pip first."
        exit 1
    fi
    
    log_success "Dependencies installed successfully!"
}

# Run tests
run_tests() {
    log_info "Running basic tests and validation..."
    cd "$PROJECT_DIR"
    
    # Check if we can import the module
    log_info "Testing module import..."
    python3 -c "import sys; sys.path.insert(0, 'src'); from unifi_documenter import __version__; print(f'Version: {__version__}')"
    
    # Check if main.py works
    log_info "Testing main script..."
    python3 main.py --help > /dev/null
    
    # Test health check
    log_info "Testing health check..."
    python3 main.py --health || true  # Allow it to fail with no config
    
    log_success "All tests passed!"
}

# Build Docker image
build_docker() {
    log_info "Building Docker image..."
    cd "$PROJECT_DIR"
    
    IMAGE_NAME="unifi-documenter-dev"
    docker build -t "$IMAGE_NAME" .
    
    log_success "Docker image built: $IMAGE_NAME"
}

# Run locally
run_local() {
    log_info "Running UniFi Documenter locally..."
    cd "$PROJECT_DIR"
    
    python3 main.py "$@"
}

# Run Docker container
run_docker() {
    log_info "Running UniFi Documenter in Docker..."
    cd "$PROJECT_DIR"
    
    IMAGE_NAME="unifi-documenter-dev"
    
    # Check if image exists
    if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
        log_warning "Docker image not found. Building..."
        build_docker
    fi
    
    # Create output directory
    mkdir -p "./output"
    
    # Run container
    docker run --rm \
        -v "$(pwd)/output:/output" \
        "$IMAGE_NAME" "$@"
}

# Health check
health_check() {
    log_info "Running health check..."
    cd "$PROJECT_DIR"
    
    # Check local
    log_info "Local health check:"
    python3 main.py --health || true
    
    # Check Docker if available
    if command -v docker &> /dev/null; then
        log_info "Docker health check:"
        run_docker --health || true
    fi
}

# Clean build artifacts
clean() {
    log_info "Cleaning build artifacts..."
    cd "$PROJECT_DIR"
    
    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    # Remove output directory
    rm -rf ./output
    
    log_success "Cleanup completed!"
}

# Main script logic
main() {
    case "${1:-help}" in
        "install")
            shift
            install_deps "$@"
            ;;
        "test")
            shift
            run_tests "$@"
            ;;
        "build")
            shift
            build_docker "$@"
            ;;
        "run")
            shift
            run_local "$@"
            ;;
        "docker")
            shift
            run_docker "$@"
            ;;
        "health")
            shift
            health_check "$@"
            ;;
        "clean")
            shift
            clean "$@"
            ;;
        "help"|"--help"|"-h")
            usage
            ;;
        *)
            log_error "Unknown command: $1"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"