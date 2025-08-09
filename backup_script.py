#!/usr/bin/env python3
"""
Main backup orchestration script for Unifi network backup automation.
Handles the overall backup process, configuration, and scheduling.
"""

import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import structlog
from dotenv import load_dotenv

from json_converter import BackupJsonConverter
from scheduler import BackupScheduler
from unifi_backup import UnifiBackupManager


class BackupOrchestrator:
    """Main orchestrator for Unifi backup operations."""

    def __init__(self):
        """Initialize the backup orchestrator with configuration."""
        load_dotenv()
        self.setup_logging()
        self.config = self.load_configuration()
        self.logger = structlog.get_logger("backup_orchestrator")
        self.running = True
        self.setup_signal_handlers()

        # Initialize components
        self.backup_manager = UnifiBackupManager(self.config)
        self.json_converter = BackupJsonConverter(self.config)
        self.scheduler = BackupScheduler(self.config)

    def setup_logging(self) -> None:
        """Configure structured logging."""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        logging.basicConfig(
            format="%(message)s", stream=sys.stdout, level=getattr(logging, log_level)
        )

    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {
            # Unifi controller settings
            "unifi_host": os.getenv("UNIFI_HOST", ""),
            "unifi_username": os.getenv("UNIFI_USERNAME", ""),
            "unifi_password": os.getenv("UNIFI_PASSWORD", ""),
            "unifi_port": int(os.getenv("UNIFI_PORT", "22")),
            # Backup settings
            "backup_schedule": os.getenv("BACKUP_SCHEDULE", "daily"),
            "backup_time": os.getenv("BACKUP_TIME", "02:00"),
            "backup_retention_days": int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
            "backup_directory": os.getenv("BACKUP_DIRECTORY", "/app/backups"),
            # Container settings
            "timezone": os.getenv("TZ", "UTC"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "health_check_port": int(os.getenv("HEALTH_CHECK_PORT", "8080")),
            # Advanced settings
            "max_retries": int(os.getenv("MAX_RETRIES", "3")),
            "retry_delay": int(os.getenv("RETRY_DELAY", "60")),
            "connection_timeout": int(os.getenv("CONNECTION_TIMEOUT", "30")),
        }

        # Validate required configuration
        required_fields = ["unifi_host", "unifi_username", "unifi_password"]
        missing_fields = [field for field in required_fields if not config[field]]

        if missing_fields:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_fields)}"
            )

        return config

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        self.logger.info("Received shutdown signal", signal=signum)
        self.running = False

    def run_backup(self) -> bool:
        """Execute a single backup operation."""
        self.logger.info("Starting backup operation")
        start_time = datetime.now()

        try:
            # Create backup directory if it doesn't exist
            backup_dir = Path(self.config["backup_directory"])
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Perform backup
            backup_file = self.backup_manager.create_backup()
            if not backup_file:
                self.logger.error("Backup creation failed")
                return False

            # Convert to JSON
            json_files = self.json_converter.convert_backup(backup_file)
            if not json_files:
                self.logger.error("JSON conversion failed")
                return False

            # Cleanup old backups
            self.cleanup_old_backups()

            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(
                "Backup operation completed successfully",
                duration_seconds=duration,
                backup_file=str(backup_file),
                json_files_count=len(json_files),
            )

            return True

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.error(
                "Backup operation failed",
                error=str(e),
                duration_seconds=duration,
                exc_info=True,
            )
            return False

    def cleanup_old_backups(self) -> None:
        """Remove backups older than retention period."""
        backup_dir = Path(self.config["backup_directory"])
        retention_days = self.config["backup_retention_days"]

        try:
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)

            for backup_file in backup_dir.rglob("*"):
                if backup_file.is_file() and backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    self.logger.info("Removed old backup file", file=str(backup_file))

        except Exception as e:
            self.logger.error("Failed to cleanup old backups", error=str(e))

    def run_scheduled(self) -> None:
        """Run in scheduled mode with cron-like scheduling."""
        self.logger.info("Starting scheduled backup mode", config=self.config)

        while self.running:
            try:
                if self.scheduler.should_run():
                    self.logger.info("Scheduled backup triggered")
                    success = self.run_backup()

                    if success:
                        self.scheduler.mark_last_run()
                    else:
                        self.logger.error("Scheduled backup failed")

                # Sleep for a minute before checking again
                time.sleep(60)

            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                self.logger.error(
                    "Error in scheduled mode", error=str(e), exc_info=True
                )
                time.sleep(60)

        self.logger.info("Scheduled backup mode stopped")

    def run_once(self) -> None:
        """Run a single backup operation and exit."""
        self.logger.info("Running single backup operation")
        success = self.run_backup()
        sys.exit(0 if success else 1)

    def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        try:
            status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "unifi_host": self.config["unifi_host"],
                    "backup_schedule": self.config["backup_schedule"],
                    "backup_time": self.config["backup_time"],
                    "backup_directory": self.config["backup_directory"],
                },
                "last_backup": self.scheduler.get_last_run(),
                "next_backup": self.scheduler.get_next_run(),
            }

            # Check if backup directory is writable
            backup_dir = Path(self.config["backup_directory"])
            backup_dir.mkdir(parents=True, exist_ok=True)
            test_file = backup_dir / "health_check.tmp"
            test_file.write_text("test")
            test_file.unlink()

            return status

        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }


def main():
    """Main entry point for the backup script."""
    try:
        orchestrator = BackupOrchestrator()

        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()

            if command == "once":
                orchestrator.run_once()
            elif command == "health":
                status = orchestrator.health_check()
                print(status)
                sys.exit(0 if status["status"] == "healthy" else 1)
            else:
                print(f"Unknown command: {command}")
                print("Usage: backup_script.py [once|health]")
                sys.exit(1)
        else:
            # Default: run in scheduled mode
            orchestrator.run_scheduled()

    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
