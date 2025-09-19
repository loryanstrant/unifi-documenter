"""
Scheduler for UniFi Documenter
"""
import schedule
import time
import logging
from datetime import datetime, timezone, date, time as dt_time
import pytz
from typing import Callable, Optional
from .config import Config

logger = logging.getLogger('unifi_documenter')

class UniFiScheduler:
    """Handles scheduling of backup processing tasks"""
    
    def __init__(self, config: Config, task_function: Callable):
        self.config = config
        self.task_function = task_function
        self.tz = pytz.timezone(config.TIMEZONE)
        self.is_running = False
        
    def _convert_time_to_utc(self, time_str: str) -> str:
        """Convert time string from configured timezone to UTC"""
        try:
            # Parse the time string (HH:MM format)
            hour, minute = map(int, time_str.split(':'))
            
            # Create a datetime for today at the specified time in the configured timezone
            today = date.today()
            target_time = dt_time(hour, minute)
            
            # Create a timezone-aware datetime
            local_dt = datetime.combine(today, target_time)
            localized_dt = self.tz.localize(local_dt)
            
            # Convert to UTC
            utc_dt = localized_dt.astimezone(pytz.UTC)
            
            # Return as HH:MM string
            return f"{utc_dt.hour:02d}:{utc_dt.minute:02d}"
            
        except Exception as e:
            logger.error(f"Failed to convert time {time_str} to UTC: {str(e)}")
            # Fallback to original time if conversion fails
            return time_str
        
    def setup_schedule(self) -> bool:
        """Setup the schedule based on configuration"""
        try:
            # Clear any existing schedules
            schedule.clear()
            
            frequency = self.config.SCHEDULE_FREQUENCY.lower()
            time_str = self.config.SCHEDULE_TIME
            
            # Convert the configured time from target timezone to UTC for the schedule library
            utc_time_str = self._convert_time_to_utc(time_str)
            
            logger.info(f"Setting up {frequency} schedule at {time_str} ({self.config.TIMEZONE})")
            logger.info(f"Converted to UTC time: {utc_time_str} for scheduling")
            
            if frequency == 'daily':
                schedule.every().day.at(utc_time_str).do(self._run_task_with_timezone)
                
            elif frequency == 'weekly':
                day_mapping = {
                    1: schedule.every().monday,
                    2: schedule.every().tuesday,
                    3: schedule.every().wednesday,
                    4: schedule.every().thursday,
                    5: schedule.every().friday,
                    6: schedule.every().saturday,
                    7: schedule.every().sunday
                }
                
                day_scheduler = day_mapping.get(self.config.SCHEDULE_DAY)
                if day_scheduler:
                    day_scheduler.at(utc_time_str).do(self._run_task_with_timezone)
                else:
                    raise ValueError(f"Invalid day for weekly schedule: {self.config.SCHEDULE_DAY}")
                    
            elif frequency == 'monthly':
                # For monthly, we'll check daily but only run on the specified day
                schedule.every().day.at(utc_time_str).do(self._run_monthly_task)
                
            else:
                raise ValueError(f"Invalid schedule frequency: {frequency}")
            
            logger.info("Schedule setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup schedule: {str(e)}")
            return False
    
    def _run_task_with_timezone(self):
        """Run the task with timezone awareness"""
        local_time = datetime.now(self.tz)
        logger.info(f"Running scheduled task at {local_time}")
        
        try:
            result = self.task_function()
            if result:
                logger.info("Scheduled task completed successfully")
            else:
                logger.error("Scheduled task failed")
        except Exception as e:
            logger.error(f"Scheduled task failed: {str(e)}")
    
    def _run_monthly_task(self):
        """Run task only if today is the configured day of the month"""
        local_time = datetime.now(self.tz)
        
        if local_time.day == self.config.SCHEDULE_DAY:
            self._run_task_with_timezone()
        else:
            logger.debug(f"Skipping monthly task - today is day {local_time.day}, "
                        f"configured for day {self.config.SCHEDULE_DAY}")
    
    def run_once(self):
        """Run the task immediately (for testing or manual execution)"""
        logger.info("Running task immediately")
        self._run_task_with_timezone()
    
    def start(self, run_immediately: bool = False):
        """Start the scheduler"""
        if not self.setup_schedule():
            raise RuntimeError("Failed to setup schedule")
        
        if run_immediately:
            logger.info("Running task immediately before starting scheduler")
            self.run_once()
        
        self.is_running = True
        logger.info("Scheduler started - waiting for scheduled tasks")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
        finally:
            self.is_running = False
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time"""
        jobs = schedule.get_jobs()
        if not jobs:
            return None
        
        next_run = min(job.next_run for job in jobs)
        
        # Convert to local timezone
        if next_run.tzinfo is None:
            next_run = self.tz.localize(next_run)
        else:
            next_run = next_run.astimezone(self.tz)
        
        return next_run
    
    def get_status(self) -> dict:
        """Get scheduler status information"""
        next_run = self.get_next_run_time()
        
        return {
            'is_running': self.is_running,
            'frequency': self.config.SCHEDULE_FREQUENCY,
            'time': self.config.SCHEDULE_TIME,
            'day': self.config.SCHEDULE_DAY if self.config.SCHEDULE_FREQUENCY in ['weekly', 'monthly'] else None,
            'timezone': self.config.TIMEZONE,
            'next_run': next_run.isoformat() if next_run else None,
            'jobs_count': len(schedule.get_jobs())
        }