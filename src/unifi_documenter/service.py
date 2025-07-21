"""
UniFi Documentation Service

This module provides the service wrapper for scheduling and managing documentation generation.
"""

import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import Config
from .documenter import UniFiDocumenter


class UniFiDocumentationService:
    """Service for scheduled UniFi documentation generation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.scheduler = None
        self.documenter = UniFiDocumenter(
            output_dir=config.unifi_output_dir,
            output_format=config.output_format
        )
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self._running = True
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self._running = False
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
    
    def start_service(self) -> None:
        """Start the documentation service"""
        self.logger.info("Starting UniFi Documentation Service")
        
        # Validate configuration
        if not self.config.validate():
            self.logger.error("Configuration validation failed")
            sys.exit(1)
        
        # Generate documentation immediately on startup
        self.logger.info("Generating initial documentation...")
        self.generate_all_documentation()
        
        # Setup scheduler for daily runs
        self._setup_scheduler()
        
        # Start scheduler
        try:
            self.logger.info("Starting scheduler...")
            self.scheduler.start()
        except KeyboardInterrupt:
            self.logger.info("Service interrupted")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
            sys.exit(1)
    
    def _setup_scheduler(self) -> None:
        """Setup the job scheduler"""
        timezone = pytz.timezone(self.config.unifi_timezone)
        self.scheduler = BlockingScheduler(timezone=timezone)
        
        # Parse schedule time
        try:
            hour, minute = map(int, self.config.unifi_schedule_time.split(':'))
        except ValueError:
            self.logger.error(f"Invalid schedule time format: {self.config.unifi_schedule_time}")
            sys.exit(1)
        
        # Add daily job
        trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)
        self.scheduler.add_job(
            func=self.generate_all_documentation,
            trigger=trigger,
            id='daily_documentation',
            name='Daily UniFi Documentation Generation',
            misfire_grace_time=300  # 5 minutes grace time
        )
        
        self.logger.info(f"Scheduled daily documentation generation at {self.config.unifi_schedule_time} {self.config.unifi_timezone}")
    
    def generate_all_documentation(self) -> None:
        """Generate documentation for all configured controllers"""
        start_time = datetime.now()
        self.logger.info("Starting documentation generation for all controllers")
        
        controllers = self.config.get_controllers()
        if not controllers:
            self.logger.error("No controllers configured")
            return
        
        total_success = 0
        total_failed = 0
        
        for controller_config in controllers:
            controller_name = controller_config.get('name', 'default')
            
            try:
                # Backup existing files
                self.documenter.backup_existing_files(controller_name)
                
                # Generate documentation
                success, result = self.documenter.generate_documentation(controller_config)
                
                if success:
                    total_success += 1
                    self.logger.info(f"Successfully generated documentation for {controller_name}: {result}")
                else:
                    total_failed += 1
                    self.logger.error(f"Failed to generate documentation for {controller_name}: {result}")
                    
            except Exception as e:
                total_failed += 1
                self.logger.error(f"Unexpected error generating documentation for {controller_name}: {e}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info(f"Documentation generation completed in {duration.total_seconds():.2f} seconds")
        self.logger.info(f"Results: {total_success} successful, {total_failed} failed")
        
        # Log summary to a status file
        self._write_status_file(start_time, end_time, total_success, total_failed)
    
    def _write_status_file(self, start_time: datetime, end_time: datetime, 
                          success_count: int, failed_count: int) -> None:
        """Write generation status to a file"""
        try:
            status_file = self.config.unifi_output_dir + '/generation-status.txt'
            with open(status_file, 'w') as f:
                f.write(f"UniFi Documentation Generation Status\n")
                f.write(f"=====================================\n\n")
                f.write(f"Start Time: {start_time.isoformat()}\n")
                f.write(f"End Time: {end_time.isoformat()}\n")
                f.write(f"Duration: {(end_time - start_time).total_seconds():.2f} seconds\n")
                f.write(f"Controllers Successful: {success_count}\n")
                f.write(f"Controllers Failed: {failed_count}\n")
                f.write(f"Total Controllers: {success_count + failed_count}\n")
                f.write(f"\nNext Scheduled Run: {self.config.unifi_schedule_time} {self.config.unifi_timezone}\n")
        except Exception as e:
            self.logger.warning(f"Failed to write status file: {e}")
    
    def run_once(self) -> bool:
        """Run documentation generation once and exit"""
        self.logger.info("Running documentation generation once...")
        
        if not self.config.validate():
            self.logger.error("Configuration validation failed")
            return False
        
        try:
            self.generate_all_documentation()
            return True
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return False
    
    def stop_service(self) -> None:
        """Stop the service"""
        self.logger.info("Stopping UniFi Documentation Service")
        self._running = False
        
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            self.logger.info("Scheduler stopped")


class ServiceHealthChecker:
    """Health checker for the service"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def check_health(self) -> Dict[str, Any]:
        """Check service health"""
        health_info = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': None,
            'controllers': [],
            'issues': []
        }
        
        try:
            # Get version information
            from . import __version__
            health_info['version'] = __version__
        except ImportError:
            health_info['issues'].append("Unable to determine version")
        
        # Check configuration
        if not self.config.validate():
            health_info['status'] = 'unhealthy'
            health_info['issues'].append("Configuration validation failed")
        
        # Check each controller configuration
        for i, controller_config in enumerate(self.config.get_controllers()):
            controller_name = controller_config.get('name', f'controller-{i}')
            controller_health = {
                'name': controller_name,
                'host': controller_config.get('host', 'unknown'),
                'status': 'unknown',
                'last_check': datetime.now().isoformat()
            }
            
            # Basic configuration check
            if self.config.validate_controller_config(controller_config):
                controller_health['status'] = 'configured'
            else:
                controller_health['status'] = 'misconfigured'
                health_info['issues'].append(f"Controller {controller_name} is misconfigured")
            
            health_info['controllers'].append(controller_health)
        
        # Overall health determination
        if health_info['issues']:
            health_info['status'] = 'degraded' if health_info['status'] == 'healthy' else 'unhealthy'
        
        return health_info
    
    def check_connectivity(self) -> Dict[str, Any]:
        """Check connectivity to all configured controllers"""
        connectivity_info = {
            'timestamp': datetime.now().isoformat(),
            'controllers': [],
            'summary': {
                'total': 0,
                'reachable': 0,
                'unreachable': 0
            }
        }
        
        for controller_config in self.config.get_controllers():
            controller_name = controller_config.get('name', 'default')
            controller_url = controller_config.get('controller_url', 'unknown')
            
            controller_connectivity = {
                'name': controller_name,
                'host': controller_url,
                'status': 'unknown',
                'response_time': None,
                'error': None
            }
            
            try:
                from .client import UniFiClient
                import time
                
                start_time = time.time()
                client = UniFiClient(
                    controller_url=controller_url,
                    username=controller_config['username'],
                    password=controller_config['password'],
                    is_udm_pro=controller_config.get('is_udm_pro', False),
                    verify_ssl=controller_config.get('verify_ssl', True),
                    api_version=controller_config.get('api_version')
                )
                
                # Attempt authentication (only username/password supported)
                success = client.authenticate()
                
                response_time = time.time() - start_time
                controller_connectivity['response_time'] = round(response_time * 1000, 2)  # ms
                
                if success:
                    controller_connectivity['status'] = 'reachable'
                    connectivity_info['summary']['reachable'] += 1
                else:
                    controller_connectivity['status'] = 'auth_failed'
                    connectivity_info['summary']['unreachable'] += 1
                    controller_connectivity['error'] = "Authentication failed"
                
                client.disconnect()
                
            except Exception as e:
                controller_connectivity['status'] = 'unreachable'
                controller_connectivity['error'] = str(e)
                connectivity_info['summary']['unreachable'] += 1
            
            connectivity_info['controllers'].append(controller_connectivity)
            connectivity_info['summary']['total'] += 1
        
        return connectivity_info