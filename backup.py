#!/usr/bin/env python3
"""
UniFi Network Backup and Documentation Tool.

This script connects to UniFi controllers, downloads backups, decrypts them,
and converts configuration data to JSON format for documentation purposes.
"""

import os
import sys
import json
import tarfile
import shutil
import logging
import subprocess
import tempfile
import struct
from datetime import datetime, timedelta
from pathlib import Path
import paramiko
import bson
import configparser
from typing import Dict, List, Optional, Any
import yaml

from decrypt_backup import UniFiBackupDecryptor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UniFiBackupManager:
    """Manages UniFi backup operations and data conversion."""
    
    def __init__(self):
        """Initialize the backup manager with environment configuration."""
        self.config = self._load_config()
        self.ssh_client = None
        self.decryptor = UniFiBackupDecryptor()
        
        # Setup directories
        self.backup_dir = Path("/backups")
        self.latest_dir = self.backup_dir / "latest"
        self.archive_dir = self.backup_dir / "archives"
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create directories
        for dir_path in [self.latest_dir, self.archive_dir, Path("/app/logs")]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {
            'host': os.getenv('UNIFI_HOST'),
            'port': int(os.getenv('UNIFI_SSH_PORT', '22')),
            'username': os.getenv('UNIFI_SSH_USER'),
            'password': os.getenv('UNIFI_SSH_PASSWORD'),
            'key_file': os.getenv('UNIFI_SSH_KEY'),
            'backup_password': os.getenv('UNIFI_BACKUP_PASSWORD', ''),
            'retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', '30')),
            'timezone': os.getenv('TZ', 'UTC'),
        }
        
        # Validate required configuration
        required_fields = ['host', 'username']
        missing_fields = [field for field in required_fields if not config[field]]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
            
        # Ensure either password or key file is provided
        if not config['password'] and not config['key_file']:
            raise ValueError("Either UNIFI_SSH_PASSWORD or UNIFI_SSH_KEY must be provided")
            
        return config
    
    def connect_ssh(self) -> paramiko.SSHClient:
        """Establish SSH connection to UniFi controller."""
        logger.info(f"Connecting to {self.config['host']}:{self.config['port']}")
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if self.config['key_file']:
                # Use SSH key authentication
                key_file = Path(self.config['key_file'])
                if not key_file.exists():
                    raise FileNotFoundError(f"SSH key file not found: {key_file}")
                    
                client.connect(
                    hostname=self.config['host'],
                    port=self.config['port'],
                    username=self.config['username'],
                    key_filename=str(key_file),
                    timeout=30
                )
            else:
                # Use password authentication
                client.connect(
                    hostname=self.config['host'],
                    port=self.config['port'],
                    username=self.config['username'],
                    password=self.config['password'],
                    timeout=30
                )
                
            logger.info("SSH connection established successfully")
            self.ssh_client = client
            return client
            
        except Exception as e:
            logger.error(f"Failed to connect via SSH: {e}")
            raise
    
    def find_latest_backup(self) -> Optional[str]:
        """Find the latest backup file on the UniFi controller."""
        if not self.ssh_client:
            self.connect_ssh()
            
        try:
            # Common backup locations on UniFi devices
            backup_paths = [
                "/data/autobackup",
                "/srv/unifi/data/backup/autobackup",
                "/var/lib/unifi/backup/autobackup",
                "/usr/lib/unifi/data/backup/autobackup"
            ]
            
            latest_backup = None
            latest_time = 0
            
            for path in backup_paths:
                stdin, stdout, stderr = self.ssh_client.exec_command(f"ls -la {path}/*.unf 2>/dev/null | tail -1")
                output = stdout.read().decode().strip()
                
                if output and not output.startswith('ls:'):
                    # Parse the ls output to get filename and timestamp
                    parts = output.split()
                    if len(parts) >= 9:
                        filename = parts[-1]
                        # Get file modification time
                        stdin, stdout, stderr = self.ssh_client.exec_command(f"stat -c %Y {filename} 2>/dev/null")
                        try:
                            file_time = int(stdout.read().decode().strip())
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_backup = filename
                        except (ValueError, IndexError):
                            continue
            
            if latest_backup:
                logger.info(f"Found latest backup: {latest_backup}")
                return latest_backup
            else:
                logger.warning("No backup files found on controller")
                return None
                
        except Exception as e:
            logger.error(f"Failed to find backup files: {e}")
            raise
    
    def download_backup(self, remote_path: str) -> str:
        """Download backup file from UniFi controller."""
        if not self.ssh_client:
            self.connect_ssh()
            
        filename = Path(remote_path).name
        local_path = self.temp_dir / filename
        
        logger.info(f"Downloading {remote_path} to {local_path}")
        
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.get(remote_path, str(local_path))
            sftp.close()
            
            logger.info(f"Download completed: {local_path}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Failed to download backup: {e}")
            raise
    
    def extract_backup(self, backup_file: str) -> str:
        """Extract the decrypted backup archive."""
        extract_dir = self.temp_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        logger.info(f"Extracting {backup_file} to {extract_dir}")
        
        try:
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(extract_dir)
                
            logger.info(f"Extraction completed: {extract_dir}")
            return str(extract_dir)
            
        except Exception as e:
            logger.error(f"Failed to extract backup: {e}")
            raise
    
    def convert_bson_to_json(self, bson_file: str, json_file: str):
        """Convert BSON file to JSON format."""
        logger.info(f"Converting {bson_file} to JSON")
        
        try:
            with open(bson_file, 'rb') as f:
                # Read BSON data
                bson_data = f.read()
                
            # Decode BSON documents
            documents = []
            offset = 0
            
            while offset < len(bson_data):
                try:
                    doc = bson.decode(bson_data[offset:])
                    documents.append(doc)
                    # Calculate next document offset
                    doc_size = struct.unpack('<I', bson_data[offset:offset+4])[0]
                    offset += doc_size
                except Exception:
                    break
            
            # Write JSON
            with open(json_file, 'w') as f:
                json.dump(documents, f, indent=2, default=str)
                
            logger.info(f"BSON conversion completed: {json_file}")
            
        except Exception as e:
            logger.error(f"Failed to convert BSON file {bson_file}: {e}")
            # Create empty JSON file as fallback
            with open(json_file, 'w') as f:
                json.dump([], f)
    
    def convert_config_files(self, extract_dir: str, output_dir: str):
        """Convert all configuration files to JSON format."""
        extract_path = Path(extract_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Converting configuration files from {extract_dir}")
        
        # Process different file types
        conversions = 0
        
        # Convert BSON files
        for bson_file in extract_path.rglob("*.bson"):
            relative_path = bson_file.relative_to(extract_path)
            json_file = output_path / relative_path.with_suffix('.json')
            json_file.parent.mkdir(parents=True, exist_ok=True)
            
            self.convert_bson_to_json(str(bson_file), str(json_file))
            conversions += 1
        
        # Convert .conf files (Java properties format)
        for conf_file in extract_path.rglob("*.conf"):
            relative_path = conf_file.relative_to(extract_path)
            json_file = output_path / relative_path.with_suffix('.json')
            json_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                config = configparser.ConfigParser()
                with open(conf_file, 'r') as f:
                    config.read_string('[DEFAULT]\n' + f.read())
                
                config_dict = dict(config['DEFAULT'])
                
                with open(json_file, 'w') as f:
                    json.dump(config_dict, f, indent=2)
                    
                conversions += 1
                logger.info(f"Converted config file: {conf_file}")
                
            except Exception as e:
                logger.warning(f"Failed to convert config file {conf_file}: {e}")
        
        # Convert .properties files
        for prop_file in extract_path.rglob("*.properties"):
            relative_path = prop_file.relative_to(extract_path)
            json_file = output_path / relative_path.with_suffix('.json')
            json_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                properties = {}
                with open(prop_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                properties[key.strip()] = value.strip()
                
                with open(json_file, 'w') as f:
                    json.dump(properties, f, indent=2)
                    
                conversions += 1
                logger.info(f"Converted properties file: {prop_file}")
                
            except Exception as e:
                logger.warning(f"Failed to convert properties file {prop_file}: {e}")
        
        # Copy existing JSON files
        for json_file in extract_path.rglob("*.json"):
            relative_path = json_file.relative_to(extract_path)
            dest_file = output_path / relative_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(json_file, dest_file)
            conversions += 1
            logger.info(f"Copied JSON file: {json_file}")
        
        # Create metadata file
        metadata = {
            'backup_date': datetime.now().isoformat(),
            'source_host': self.config['host'],
            'files_converted': conversions,
            'conversion_timestamp': datetime.now().isoformat()
        }
        
        with open(output_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Configuration conversion completed. {conversions} files processed.")
    
    def setup_git_repo(self, repo_path: str):
        """Initialize and configure Git repository for backup versioning."""
        repo = Path(repo_path)
        
        if not (repo / '.git').exists():
            logger.info(f"Initializing Git repository at {repo_path}")
            subprocess.run(['git', 'init'], cwd=repo_path, check=True)
            
            # Create initial .gitignore
            gitignore_content = """
# Ignore temporary files
*.tmp
*.log

# Ignore sensitive data
*.key
*.pem
credentials/
"""
            with open(repo / '.gitignore', 'w') as f:
                f.write(gitignore_content.strip())
    
    def commit_backup(self, backup_path: str):
        """Commit backup changes to Git."""
        logger.info(f"Committing backup changes in {backup_path}")
        
        try:
            # Add all files
            subprocess.run(['git', 'add', '.'], cwd=backup_path, check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(['git', 'diff', '--staged', '--quiet'], 
                                  cwd=backup_path, capture_output=True)
            
            if result.returncode != 0:  # There are changes
                commit_message = f"Backup update - {datetime.now().isoformat()}"
                subprocess.run(['git', 'commit', '-m', commit_message], 
                             cwd=backup_path, check=True)
                logger.info("Changes committed to Git")
            else:
                logger.info("No changes detected, skipping commit")
                
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git commit failed: {e}")
    
    def cleanup_old_backups(self):
        """Remove old backup archives based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.config['retention_days'])
        logger.info(f"Cleaning up backups older than {cutoff_date}")
        
        removed_count = 0
        
        for backup_file in self.archive_dir.glob("backup_*.tar.gz"):
            try:
                file_stat = backup_file.stat()
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup_file}")
                    
            except Exception as e:
                logger.warning(f"Failed to process backup file {backup_file}: {e}")
        
        logger.info(f"Cleanup completed. Removed {removed_count} old backups.")
    
    def run_backup(self):
        """Execute the complete backup process."""
        try:
            logger.info("Starting UniFi backup process")
            
            # Connect to controller
            self.connect_ssh()
            
            # Find and download latest backup
            remote_backup = self.find_latest_backup()
            if not remote_backup:
                logger.error("No backup file found on controller")
                return False
            
            local_backup = self.download_backup(remote_backup)
            
            # Decrypt backup
            decrypted_backup = self.decryptor.decrypt_backup(local_backup)
            
            # Extract backup
            extract_dir = self.extract_backup(decrypted_backup)
            
            # Convert configuration files
            self.convert_config_files(extract_dir, str(self.latest_dir))
            
            # Setup Git repository
            self.setup_git_repo(str(self.latest_dir))
            
            # Commit changes
            self.commit_backup(str(self.latest_dir))
            
            # Archive the backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"backup_{timestamp}.tar.gz"
            archive_path = self.archive_dir / archive_name
            
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(self.latest_dir, arcname='backup')
            
            logger.info(f"Backup archived to {archive_path}")
            
            # Cleanup old backups
            self.cleanup_old_backups()
            
            logger.info("Backup process completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Backup process failed: {e}")
            return False
            
        finally:
            # Cleanup
            if self.ssh_client:
                self.ssh_client.close()
            
            # Remove temporary directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

def main():
    """Main entry point for the backup script."""
    try:
        manager = UniFiBackupManager()
        success = manager.run_backup()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()