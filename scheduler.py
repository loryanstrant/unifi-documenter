#!/usr/bin/env python3
"""
Scheduling management for automated Unifi backup operations.
Handles cron-like scheduling and tracks backup execution times.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from croniter import croniter


class BackupScheduler:
    """Manages backup scheduling and execution tracking."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the scheduler with configuration."""
        self.config = config
        self.logger = structlog.get_logger("backup_scheduler")
        self.state_file = (
            Path(config.get("backup_directory", "/app/backups"))
            / ".scheduler_state.json"
        )
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load scheduler state from persistent storage."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                self.logger.debug("Loaded scheduler state", state=state)
                return state
            else:
                self.logger.info(
                    "No existing scheduler state found, initializing new state"
                )
                return {
                    "last_run": None,
                    "next_run": None,
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "created": datetime.now().isoformat(),
                }
        except Exception as e:
            self.logger.error("Error loading scheduler state", error=str(e))
            return {
                "last_run": None,
                "next_run": None,
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "created": datetime.now().isoformat(),
            }

    def _save_state(self) -> None:
        """Save scheduler state to persistent storage."""
        try:
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            # Update state with current timestamp
            self.state["updated"] = datetime.now().isoformat()

            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2, default=str)

            self.logger.debug("Saved scheduler state")

        except Exception as e:
            self.logger.error("Error saving scheduler state", error=str(e))

    def _get_cron_expression(self) -> str:
        """Generate cron expression based on configuration."""
        schedule = self.config.get("backup_schedule", "daily").lower()
        backup_time = self.config.get("backup_time", "02:00")

        try:
            # Parse time (HH:MM format)
            time_parts = backup_time.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

            # Validate time
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                self.logger.warning(
                    "Invalid backup time, using default 02:00", backup_time=backup_time
                )
                hour, minute = 2, 0

        except (ValueError, IndexError):
            self.logger.warning(
                "Invalid backup time format, using default 02:00",
                backup_time=backup_time,
            )
            hour, minute = 2, 0

        # Generate cron expression
        if schedule == "daily":
            cron_expr = f"{minute} {hour} * * *"
        elif schedule == "weekly":
            # Run on Sunday by default
            cron_expr = f"{minute} {hour} * * 0"
        elif schedule.startswith("cron:"):
            # Custom cron expression
            cron_expr = schedule[5:].strip()
        else:
            self.logger.warning("Unknown schedule type, using daily", schedule=schedule)
            cron_expr = f"{minute} {hour} * * *"

        self.logger.info(
            "Generated cron expression", expression=cron_expr, schedule=schedule
        )
        return cron_expr

    def _calculate_next_run(self) -> datetime:
        """Calculate the next scheduled run time."""
        try:
            cron_expr = self._get_cron_expression()
            cron = croniter(cron_expr, datetime.now())
            next_run = cron.get_next(datetime)

            self.logger.debug("Calculated next run time", next_run=next_run.isoformat())
            return next_run

        except Exception as e:
            self.logger.error("Error calculating next run time", error=str(e))
            # Fallback: next day at configured time
            backup_time = self.config.get("backup_time", "02:00")
            time_parts = backup_time.split(":")
            hour = int(time_parts[0]) if time_parts[0].isdigit() else 2
            minute = (
                int(time_parts[1])
                if len(time_parts) > 1 and time_parts[1].isdigit()
                else 0
            )

            next_run = datetime.now().replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            if next_run <= datetime.now():
                next_run += timedelta(days=1)

            return next_run

    def should_run(self) -> bool:
        """Check if a backup should be executed now."""
        try:
            current_time = datetime.now()

            # If no next run time is set, calculate it
            if not self.state.get("next_run"):
                self.state["next_run"] = self._calculate_next_run().isoformat()
                self._save_state()

            next_run_str = self.state.get("next_run")
            if not next_run_str:
                return False

            try:
                next_run = datetime.fromisoformat(next_run_str)
            except ValueError:
                # Handle older datetime formats
                next_run = datetime.strptime(next_run_str, "%Y-%m-%dT%H:%M:%S.%f")

            should_run = current_time >= next_run

            if should_run:
                self.logger.info(
                    "Backup should run now",
                    current_time=current_time.isoformat(),
                    scheduled_time=next_run.isoformat(),
                )
            else:
                time_until_next = next_run - current_time
                self.logger.debug(
                    "Backup not due yet",
                    time_until_next=str(time_until_next),
                    next_run=next_run.isoformat(),
                )

            return should_run

        except Exception as e:
            self.logger.error("Error checking if backup should run", error=str(e))
            return False

    def mark_last_run(self, success: bool = True) -> None:
        """Mark the completion of a backup run."""
        try:
            current_time = datetime.now()

            self.state["last_run"] = current_time.isoformat()
            self.state["total_runs"] = self.state.get("total_runs", 0) + 1

            if success:
                self.state["successful_runs"] = self.state.get("successful_runs", 0) + 1
                self.logger.info(
                    "Marked successful backup run", run_time=current_time.isoformat()
                )
            else:
                self.state["failed_runs"] = self.state.get("failed_runs", 0) + 1
                self.logger.warning(
                    "Marked failed backup run", run_time=current_time.isoformat()
                )

            # Calculate next run time
            self.state["next_run"] = self._calculate_next_run().isoformat()

            # Add some statistics
            success_rate = (
                (self.state["successful_runs"] / self.state["total_runs"]) * 100
                if self.state["total_runs"] > 0
                else 0
            )
            self.state["success_rate"] = round(success_rate, 2)

            self._save_state()

            self.logger.info(
                "Updated backup statistics",
                total_runs=self.state["total_runs"],
                successful_runs=self.state["successful_runs"],
                failed_runs=self.state["failed_runs"],
                success_rate=self.state["success_rate"],
                next_run=self.state["next_run"],
            )

        except Exception as e:
            self.logger.error("Error marking backup run completion", error=str(e))

    def get_last_run(self) -> Optional[str]:
        """Get the timestamp of the last backup run."""
        return self.state.get("last_run")

    def get_next_run(self) -> Optional[str]:
        """Get the timestamp of the next scheduled backup run."""
        next_run = self.state.get("next_run")
        if not next_run:
            next_run = self._calculate_next_run().isoformat()
            self.state["next_run"] = next_run
            self._save_state()
        return next_run

    def get_statistics(self) -> Dict[str, Any]:
        """Get backup execution statistics."""
        return {
            "total_runs": self.state.get("total_runs", 0),
            "successful_runs": self.state.get("successful_runs", 0),
            "failed_runs": self.state.get("failed_runs", 0),
            "success_rate": self.state.get("success_rate", 0),
            "last_run": self.state.get("last_run"),
            "next_run": self.state.get("next_run"),
            "created": self.state.get("created"),
            "updated": self.state.get("updated"),
        }

    def force_next_run(self, when: Optional[datetime] = None) -> None:
        """Force the next backup run to occur at a specific time."""
        if when is None:
            when = datetime.now() + timedelta(minutes=1)

        self.state["next_run"] = when.isoformat()
        self._save_state()

        self.logger.info("Forced next backup run", next_run=when.isoformat())

    def reset_schedule(self) -> None:
        """Reset the schedule and calculate new run times."""
        self.state["next_run"] = self._calculate_next_run().isoformat()
        self._save_state()

        self.logger.info("Reset backup schedule", next_run=self.state["next_run"])

    def is_overdue(self, threshold_hours: int = 25) -> bool:
        """Check if a backup is overdue based on the threshold."""
        try:
            last_run_str = self.state.get("last_run")
            if not last_run_str:
                # No previous run, consider it overdue
                return True

            try:
                last_run = datetime.fromisoformat(last_run_str)
            except ValueError:
                last_run = datetime.strptime(last_run_str, "%Y-%m-%dT%H:%M:%S.%f")

            time_since_last = datetime.now() - last_run
            overdue = time_since_last.total_seconds() / 3600 > threshold_hours

            if overdue:
                self.logger.warning(
                    "Backup is overdue",
                    last_run=last_run.isoformat(),
                    hours_since_last=time_since_last.total_seconds() / 3600,
                    threshold_hours=threshold_hours,
                )

            return overdue

        except Exception as e:
            self.logger.error("Error checking if backup is overdue", error=str(e))
            return True  # Assume overdue if we can't determine

    def get_schedule_info(self) -> Dict[str, Any]:
        """Get comprehensive schedule information."""
        try:
            cron_expr = self._get_cron_expression()
            next_run = self.get_next_run()
            last_run = self.get_last_run()

            schedule_info = {
                "cron_expression": cron_expr,
                "schedule_type": self.config.get("backup_schedule", "daily"),
                "backup_time": self.config.get("backup_time", "02:00"),
                "timezone": self.config.get("timezone", "UTC"),
                "next_run": next_run,
                "last_run": last_run,
                "is_overdue": self.is_overdue(),
                "statistics": self.get_statistics(),
            }

            if next_run:
                try:
                    next_run_dt = datetime.fromisoformat(next_run)
                    time_until_next = next_run_dt - datetime.now()
                    schedule_info["time_until_next_run"] = str(time_until_next)
                except ValueError:
                    pass

            return schedule_info

        except Exception as e:
            self.logger.error("Error getting schedule info", error=str(e))
            return {
                "error": str(e),
                "schedule_type": self.config.get("backup_schedule", "daily"),
                "backup_time": self.config.get("backup_time", "02:00"),
            }
