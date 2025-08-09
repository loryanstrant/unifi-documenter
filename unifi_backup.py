#!/usr/bin/env python3
"""
Unifi-specific backup logic for connecting to controllers and downloading backups.
Handles SSH connections, backup file discovery, and download operations.
"""

import io
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import paramiko
import structlog
from paramiko.ssh_exception import AuthenticationException, SSHException


class UnifiBackupManager:
    """Manages Unifi controller backup operations via SSH."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the backup manager with configuration."""
        self.config = config
        self.logger = structlog.get_logger("unifi_backup")
        self.ssh_client = None

    def _connect_ssh(self) -> bool:
        """Establish SSH connection to Unifi controller."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.logger.info(
                "Connecting to Unifi controller",
                host=self.config["unifi_host"],
                port=self.config["unifi_port"],
                username=self.config["unifi_username"],
            )

            self.ssh_client.connect(
                hostname=self.config["unifi_host"],
                port=self.config["unifi_port"],
                username=self.config["unifi_username"],
                password=self.config["unifi_password"],
                timeout=self.config["connection_timeout"],
                allow_agent=False,
                look_for_keys=False,
            )

            self.logger.info("SSH connection established successfully")
            return True

        except AuthenticationException as e:
            self.logger.error("SSH authentication failed", error=str(e))
            return False
        except SSHException as e:
            self.logger.error("SSH connection failed", error=str(e))
            return False
        except Exception as e:
            self.logger.error("Unexpected error during SSH connection", error=str(e))
            return False

    def _disconnect_ssh(self) -> None:
        """Close SSH connection."""
        if self.ssh_client:
            try:
                self.ssh_client.close()
                self.logger.info("SSH connection closed")
            except Exception as e:
                self.logger.warning("Error closing SSH connection", error=str(e))
            finally:
                self.ssh_client = None

    def _execute_command(self, command: str) -> Tuple[bool, str, str]:
        """Execute a command via SSH and return success status, stdout, stderr."""
        try:
            self.logger.debug("Executing SSH command", command=command)

            stdin, stdout, stderr = self.ssh_client.exec_command(command)

            stdout_data = stdout.read().decode("utf-8")
            stderr_data = stderr.read().decode("utf-8")
            exit_status = stdout.channel.recv_exit_status()

            success = exit_status == 0

            if not success:
                self.logger.warning(
                    "Command execution failed",
                    command=command,
                    exit_status=exit_status,
                    stderr=stderr_data,
                )
            else:
                self.logger.debug("Command executed successfully", command=command)

            return success, stdout_data, stderr_data

        except Exception as e:
            self.logger.error(
                "Error executing SSH command", command=command, error=str(e)
            )
            return False, "", str(e)

    def _find_backup_files(self) -> List[Dict[str, Any]]:
        """Find available backup files on the Unifi controller."""
        backup_paths = [
            "/usr/lib/unifi/data/backup/autobackup",
            "/data/autobackup",
            "/opt/unifi/data/backup/autobackup",
            "/var/lib/unifi/backup/autobackup",
        ]

        backup_files = []

        for backup_path in backup_paths:
            success, stdout, stderr = self._execute_command(
                f"ls -la {backup_path}/ 2>/dev/null || echo 'PATH_NOT_FOUND'"
            )

            if success and "PATH_NOT_FOUND" not in stdout:
                self.logger.info("Found backup directory", path=backup_path)

                # Parse backup files from ls output
                for line in stdout.strip().split("\n"):
                    if line.startswith("-") and ".unf" in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            filename = parts[-1]
                            size = int(parts[4])

                            # Extract timestamp from filename if possible
                            timestamp_match = re.search(
                                r"(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})", filename
                            )
                            if timestamp_match:
                                date_str = f"{timestamp_match.group(1)} {timestamp_match.group(2)}:{timestamp_match.group(3)}:{timestamp_match.group(4)}"
                                try:
                                    file_timestamp = datetime.strptime(
                                        date_str, "%Y-%m-%d %H:%M:%S"
                                    )
                                except ValueError:
                                    file_timestamp = datetime.now()
                            else:
                                file_timestamp = datetime.now()

                            backup_files.append(
                                {
                                    "path": f"{backup_path}/{filename}",
                                    "filename": filename,
                                    "size": size,
                                    "timestamp": file_timestamp,
                                    "directory": backup_path,
                                }
                            )

                if backup_files:
                    break

        # Sort by timestamp, newest first
        backup_files.sort(key=lambda x: x["timestamp"], reverse=True)

        self.logger.info("Found backup files", count=len(backup_files))
        for backup_file in backup_files[:5]:  # Log first 5 files
            self.logger.debug(
                "Backup file found",
                filename=backup_file["filename"],
                size=backup_file["size"],
                timestamp=backup_file["timestamp"].isoformat(),
            )

        return backup_files

    def _download_backup_file(self, remote_path: str, local_path: Path) -> bool:
        """Download a backup file from the Unifi controller."""
        try:
            self.logger.info(
                "Downloading backup file",
                remote_path=remote_path,
                local_path=str(local_path),
            )

            sftp = self.ssh_client.open_sftp()

            # Get file size for progress tracking
            file_attrs = sftp.stat(remote_path)
            file_size = file_attrs.st_size

            self.logger.info("Starting download", file_size=file_size)

            # Download the file
            sftp.get(remote_path, str(local_path))

            # Verify download
            if local_path.exists() and local_path.stat().st_size == file_size:
                self.logger.info("Download completed successfully")
                return True
            else:
                self.logger.error("Download verification failed")
                return False

        except Exception as e:
            self.logger.error("Error downloading backup file", error=str(e))
            return False
        finally:
            try:
                sftp.close()
            except:
                pass

    def _get_device_info(self) -> Dict[str, Any]:
        """Get device information from the Unifi controller."""
        device_info = {}

        # Try to get system information
        success, stdout, stderr = self._execute_command(
            "cat /etc/hostname 2>/dev/null || echo 'unknown'"
        )
        if success:
            device_info["hostname"] = stdout.strip()

        # Try to get Unifi version
        success, stdout, stderr = self._execute_command(
            "dpkg -l | grep unifi | head -1"
        )
        if success and stdout:
            parts = stdout.split()
            if len(parts) >= 3:
                device_info["unifi_version"] = parts[2]

        # Try to get system info
        success, stdout, stderr = self._execute_command("uname -a")
        if success:
            device_info["system_info"] = stdout.strip()

        # Try to get uptime
        success, stdout, stderr = self._execute_command("uptime")
        if success:
            device_info["uptime"] = stdout.strip()

        return device_info

    def create_backup(self) -> Optional[Path]:
        """Create a new backup by downloading the latest backup file."""
        try:
            # Connect to SSH
            if not self._connect_ssh():
                return None

            # Get device information
            device_info = self._get_device_info()
            self.logger.info("Connected to device", device_info=device_info)

            # Find available backup files
            backup_files = self._find_backup_files()

            if not backup_files:
                self.logger.error("No backup files found on controller")
                return None

            # Select the most recent backup
            latest_backup = backup_files[0]
            self.logger.info(
                "Selected latest backup",
                filename=latest_backup["filename"],
                timestamp=latest_backup["timestamp"].isoformat(),
                size=latest_backup["size"],
            )

            # Create local backup directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_base_dir = Path(self.config["backup_directory"])
            backup_dir = backup_base_dir / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Download the backup file
            local_backup_path = backup_dir / latest_backup["filename"]

            success = self._download_backup_file(
                latest_backup["path"], local_backup_path
            )

            if not success:
                self.logger.error("Failed to download backup file")
                return None

            # Save device information
            device_info_file = backup_dir / "device_info.json"
            import json

            with open(device_info_file, "w") as f:
                json.dump(
                    {
                        "device_info": device_info,
                        "backup_info": latest_backup,
                        "download_timestamp": datetime.now().isoformat(),
                        "controller_host": self.config["unifi_host"],
                    },
                    f,
                    indent=2,
                    default=str,
                )

            self.logger.info(
                "Backup created successfully",
                backup_path=str(local_backup_path),
                backup_directory=str(backup_dir),
            )

            return local_backup_path

        except Exception as e:
            self.logger.error("Error creating backup", error=str(e), exc_info=True)
            return None
        finally:
            self._disconnect_ssh()

    def test_connection(self) -> bool:
        """Test SSH connection to the Unifi controller."""
        try:
            if not self._connect_ssh():
                return False

            # Test basic command execution
            success, stdout, stderr = self._execute_command("echo 'connection_test'")

            if success and "connection_test" in stdout:
                self.logger.info("Connection test successful")
                return True
            else:
                self.logger.error("Connection test failed")
                return False

        except Exception as e:
            self.logger.error("Connection test error", error=str(e))
            return False
        finally:
            self._disconnect_ssh()

    def list_available_backups(self) -> List[Dict[str, Any]]:
        """List all available backup files on the controller."""
        try:
            if not self._connect_ssh():
                return []

            backup_files = self._find_backup_files()
            return backup_files

        except Exception as e:
            self.logger.error("Error listing backups", error=str(e))
            return []
        finally:
            self._disconnect_ssh()
