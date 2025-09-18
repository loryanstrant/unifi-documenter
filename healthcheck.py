#!/usr/bin/env python3
"""
Health check script for UniFi Documenter container
"""
import sys
import os
import json
from pathlib import Path

def check_health():
    """Check if the application is healthy"""
    try:
        # Check if output directory is writable
        output_dir = Path('/app/output')
        if not output_dir.exists() or not os.access(output_dir, os.W_OK):
            return False, "Output directory not accessible"
        
        # Check if log file exists and is recent (within last hour)
        log_file = output_dir / 'unifi-documenter.log'
        if log_file.exists():
            import time
            last_modified = log_file.stat().st_mtime
            if time.time() - last_modified > 3600:  # 1 hour
                return False, "Log file is too old"
        
        # Check if configuration is valid
        sys.path.insert(0, '/app')
        try:
            from src.config import Config
            Config.validate()
        except Exception as e:
            return False, f"Configuration invalid: {str(e)}"
        
        return True, "Healthy"
        
    except Exception as e:
        return False, f"Health check failed: {str(e)}"

if __name__ == "__main__":
    healthy, message = check_health()
    print(f"Health: {message}")
    sys.exit(0 if healthy else 1)