"""
Main application entry point for UniFi Documenter
"""
import os
import sys
import logging
import signal
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config
from src.utils import setup_logging
from src.backup_processor import UniFiBackupProcessor
from src.backup_analyzer import UniFiBackupAnalyzer
from src.scheduler import UniFiScheduler

logger = logging.getLogger('unifi_documenter')

class UniFiDocumenter:
    """Main application class for UniFi Documenter"""
    
    def __init__(self):
        self.config = None
        self.scheduler = None
        self.shutdown_requested = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        if self.scheduler:
            self.scheduler.stop()
    
    def initialize(self) -> bool:
        """Initialize the application"""
        try:
            # Setup logging
            log_file = os.path.join(Config.OUTPUT_DIR, 'unifi-documenter.log')
            os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
            setup_logging("INFO", log_file)
            
            logger.info("Starting UniFi Documenter")
            logger.info(f"Output directory: {Config.OUTPUT_DIR}")
            
            # Validate configuration
            self.config = Config()
            if not self.config.validate():
                return False
            
            logger.info(f"Configuration validated successfully")
            logger.info(f"Schedule: {self.config.SCHEDULE_FREQUENCY} at {self.config.SCHEDULE_TIME} ({self.config.TIMEZONE})")
            logger.info(f"AI Provider: {self.config.AI_PROVIDER}")
            
            return True
            
        except Exception as e:
            print(f"Initialization failed: {str(e)}")
            return False
    
    def run_backup_and_analysis(self) -> bool:
        """Run the complete backup and analysis pipeline"""
        try:
            logger.info("Starting backup and analysis pipeline")
            
            # Process backup
            with UniFiBackupProcessor(self.config) as processor:
                backup_result = processor.process_backup()
                
                if not backup_result:
                    logger.error("Backup processing failed")
                    return False
            
            # Analyze backup data
            analyzer = UniFiBackupAnalyzer(self.config)
            analysis_result = analyzer.analyze_backup_data(backup_result)
            
            if not analysis_result:
                logger.error("Backup analysis failed")
                return False
            
            logger.info(f"Pipeline completed successfully")
            logger.info(f"Analysis results saved to: {analysis_result['analysis_dir']}")
            logger.info(f"Generated documentation for {analysis_result['total_documents']} documents")
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            return False
    
    def run_scheduled(self, run_immediately: bool = False) -> None:
        """Run the application in scheduled mode"""
        try:
            # Create scheduler
            self.scheduler = UniFiScheduler(self.config, self.run_backup_and_analysis)
            
            # Log schedule information
            status = self.scheduler.get_status()
            logger.info(f"Scheduler configured: {status}")
            
            if run_immediately:
                logger.info("Running initial backup and analysis...")
                self.run_backup_and_analysis()
            
            # Start scheduler
            logger.info("Starting scheduler...")
            self.scheduler.start(run_immediately=False)  # Don't run again if we just ran
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
        finally:
            if self.scheduler:
                self.scheduler.stop()
    
    def run_once(self) -> bool:
        """Run the backup and analysis once and exit"""
        logger.info("Running in single execution mode")
        return self.run_backup_and_analysis()

def main():
    """Main entry point"""
    app = UniFiDocumenter()
    
    if not app.initialize():
        sys.exit(1)
    
    # Check command line arguments
    run_mode = os.getenv('RUN_MODE', 'scheduled').lower()
    run_immediately = os.getenv('RUN_IMMEDIATELY', 'false').lower() == 'true'
    
    try:
        if run_mode == 'once':
            success = app.run_once()
            sys.exit(0 if success else 1)
        else:
            app.run_scheduled(run_immediately=run_immediately)
            
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()