"""
Logging utilities for UniFi Documenter
"""
import logging
import sys
from datetime import datetime
import pytz
from pathlib import Path

def get_timezone_aware_now(config):
    """Get current datetime in configured timezone"""
    try:
        tz = pytz.timezone(config.TIMEZONE)
        return datetime.now(tz)
    except:
        return datetime.now()


def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('unifi_documenter')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_execution_time(func):
    """Decorator to log function execution time"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('unifi_documenter')
        start_time = datetime.now()
        logger.info(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = end_time - start_time
            logger.info(f"Completed {func.__name__} in {duration.total_seconds():.2f} seconds")
            return result
        except Exception as e:
            end_time = datetime.now()
            duration = end_time - start_time
            logger.error(f"Failed {func.__name__} after {duration.total_seconds():.2f} seconds: {str(e)}")
            raise
    
    return wrapper