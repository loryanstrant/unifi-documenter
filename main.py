#!/usr/bin/env python3
"""
UniFi Documentation Service - Main Entry Point

This service continuously generates documentation for UniFi networks including:
- Networks & VLANs
- WiFi Networks  
- Configuration Settings
- Users & Clients
- UniFi Devices
- IP Addressing
- Firewall Rules
- NAT Rules
- Other relevant data

The service supports multiple UniFi controllers and runs on a configurable schedule.
"""

import sys
import os
import logging
import argparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unifi_documenter.service import UniFiDocumentationService, ServiceHealthChecker
from unifi_documenter.config import Config


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter with timezone-aware timestamps
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from external libraries
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='UniFi Network Documentation Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run as a service (default)
  python main.py
  
  # Run once and exit
  python main.py --run-once
  
  # Check health
  python main.py --health
  
  # Check connectivity to controllers
  python main.py --check-connectivity
  
  # Use custom config file
  python main.py --config config.yml
  
  # Enable verbose logging
  python main.py --verbose

Environment Variables:
  UNIFI_CONTROLLER_URL     - Full URL of UniFi controller (e.g., https://unifi.example.com:8443)
  UNIFI_USERNAME          - Local admin username for authentication
  UNIFI_PASSWORD          - Password for authentication
  UNIFI_IS_UDM_PRO        - Set to true for UniFi OS based controllers (default: false)
  UNIFI_API_VERSION       - UniFi API version (auto-detected if not specified)
  UNIFI_VERIFY_SSL        - Verify SSL certificates (default: true)
  UNIFI_TIMEZONE          - Timezone for scheduling (default: UTC)
  UNIFI_SCHEDULE_TIME     - Daily run time (default: 02:00)
  UNIFI_OUTPUT_DIR        - Output directory (default: /output)
  UNIFI_OUTPUT_FORMAT     - Output format: markdown/json (default: markdown)
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Configuration file path (JSON or YAML)'
    )
    
    parser.add_argument(
        '--run-once', 
        action='store_true',
        help='Run documentation generation once and exit'
    )
    
    parser.add_argument(
        '--health',
        action='store_true', 
        help='Check service health and exit'
    )
    
    parser.add_argument(
        '--check-connectivity',
        action='store_true',
        help='Check connectivity to all configured controllers and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser


def main():
    """
    Start the UniFi Documentation Service.
    
    The service will:
    1. Load configuration from environment variables and/or config file
    2. Generate documentation immediately on startup (unless --health or --check-connectivity)
    3. Schedule daily documentation generation (unless --run-once)
    4. Keep running to maintain the schedule (unless --run-once)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    verbose = args.verbose or os.getenv('UNIFI_VERBOSE', '').lower() in ['true', '1', 'yes', 'on']
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting UniFi Documentation Service")
        
        # Load configuration
        config = Config(args.config)
        
        # Handle health check
        if args.health:
            health_checker = ServiceHealthChecker(config)
            health_info = health_checker.check_health()
            
            print(f"Service Health: {health_info['status'].upper()}")
            print(f"Version: {health_info.get('version', 'Unknown')}")
            print(f"Controllers: {len(health_info['controllers'])}")
            
            if health_info['issues']:
                print("\nIssues:")
                for issue in health_info['issues']:
                    print(f"  - {issue}")
            
            if health_info['controllers']:
                print("\nControllers:")
                for controller in health_info['controllers']:
                    print(f"  - {controller['name']} ({controller['host']}): {controller['status']}")
            
            sys.exit(0 if health_info['status'] in ['healthy', 'degraded'] else 1)
        
        # Handle connectivity check
        if args.check_connectivity:
            health_checker = ServiceHealthChecker(config)
            connectivity_info = health_checker.check_connectivity()
            
            summary = connectivity_info['summary']
            print(f"Connectivity Check: {summary['reachable']}/{summary['total']} controllers reachable")
            
            for controller in connectivity_info['controllers']:
                status_icon = "✓" if controller['status'] == 'reachable' else "✗"
                response_time = f" ({controller['response_time']}ms)" if controller['response_time'] else ""
                error_msg = f" - {controller['error']}" if controller['error'] else ""
                
                print(f"  {status_icon} {controller['name']} ({controller['host']}): {controller['status']}{response_time}{error_msg}")
            
            sys.exit(0 if summary['unreachable'] == 0 else 1)
        
        # Log configuration info (without sensitive data)
        logger.info(f"Service configuration:")
        logger.info(f"  - Timezone: {config.unifi_timezone}")
        logger.info(f"  - Schedule: {config.unifi_schedule_time}")
        logger.info(f"  - Output directory: {config.unifi_output_dir}")
        logger.info(f"  - Output format: {config.output_format}")
        logger.info(f"  - Configured controllers: {len(config.get_controllers())}")
        
        # Create and start service
        service = UniFiDocumentationService(config)
        
        if args.run_once:
            # Run once and exit
            logger.info("Running documentation generation once...")
            success = service.run_once()
            sys.exit(0 if success else 1)
        else:
            # Run as a service
            service.start_service()
        
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Service startup failed: {e}")
        if verbose:
            logger.exception("Full exception details:")
        sys.exit(1)


if __name__ == '__main__':
    main()