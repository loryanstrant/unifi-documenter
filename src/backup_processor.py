"""
UniFi backup processor - converts and extracts backup files
"""
import os
import json
import gzip
import shutil
import tempfile
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import paramiko
import logging

from .utils import log_execution_time
from .config import Config

logger = logging.getLogger('unifi_documenter')

class UniFiBackupProcessor:
    """Handles downloading, decrypting, and processing UniFi backup files"""
    
    def __init__(self, config: Config):
        self.config = config
        self.ssh_client = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.ssh_client:
            self.ssh_client.close()
    
    @log_execution_time
    def connect_to_udm(self) -> bool:
        """Establish SSH connection to UDM"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.config.UDM_IP,
                username='root',
                password=self.config.UDM_ROOT_PASSWORD,
                timeout=30
            )
            
            logger.info(f"Successfully connected to UDM at {self.config.UDM_IP}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to UDM: {str(e)}")
            return False
    
    @log_execution_time
    def get_latest_backup_file(self) -> Optional[str]:
        """Find the latest .unf backup file on the UDM"""
        if not self.ssh_client:
            if not self.connect_to_udm():
                return None
        
        try:
            command = f"ls -t {self.config.REMOTE_BACKUP_DIR}/*.unf 2>/dev/null | head -n 1"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            
            latest_file = stdout.read().decode().strip()
            error_output = stderr.read().decode().strip()
            
            if error_output or not latest_file:
                logger.error(f"No .unf files found in {self.config.REMOTE_BACKUP_DIR}")
                return None
            
            logger.info(f"Latest backup file identified: {latest_file}")
            return latest_file
            
        except Exception as e:
            logger.error(f"Failed to find latest backup file: {str(e)}")
            return None
    
    @log_execution_time
    def download_backup_file(self, remote_file: str, local_path: str) -> bool:
        """Download backup file from UDM to local storage"""
        if not self.ssh_client:
            if not self.connect_to_udm():
                return False
        
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.get(remote_file, local_path)
            sftp.close()
            
            logger.info(f"Backup file downloaded to {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download backup file: {str(e)}")
            return False
    
    @log_execution_time
    def decrypt_unf_file(self, encrypted_file: str, output_file: str) -> bool:
        """Decrypt .unf file to ZIP format"""
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_filename = tmp_file.name
            
            # Decrypt using OpenSSL
            decrypt_cmd = [
                'openssl', 'enc', '-d',
                '-in', encrypted_file,
                '-out', tmp_filename,
                '-aes-128-cbc',
                '-K', '626379616e676b6d6c756f686d617273',
                '-iv', '75626e74656e74657270726973656170',
                '-nopad'
            ]
            
            result = subprocess.run(decrypt_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"OpenSSL decryption failed: {result.stderr}")
                return False
            
            # Fix ZIP file using zip command
            fix_cmd = ['zip', '-FF', tmp_filename, '--out', output_file]
            result = subprocess.run(fix_cmd, input='y\n', capture_output=True, text=True)
            
            # Clean up temporary file
            os.unlink(tmp_filename)
            
            if result.returncode != 0:
                logger.error(f"ZIP fix failed: {result.stderr}")
                return False
            
            if not os.path.exists(output_file):
                logger.error("Decrypted ZIP file was not created")
                return False
            
            logger.info(f".unf file decrypted successfully to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            return False
    
    @log_execution_time
    def extract_zip_file(self, zip_file: str, extract_dir: str) -> bool:
        """Extract ZIP file contents"""
        try:
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            logger.info(f"ZIP file extracted to {extract_dir}")
            return True
            
        except Exception as e:
            logger.error(f"ZIP extraction failed: {str(e)}")
            return False
    
    @log_execution_time
    def find_and_decompress_db(self, extract_dir: str) -> Optional[str]:
        """Find db.gz file and decompress it"""
        try:
            # Find db.gz file
            db_gz_files = list(Path(extract_dir).rglob("db.gz"))
            
            if not db_gz_files:
                logger.error("No db.gz file found in extracted contents")
                return None
            
            db_gz_file = str(db_gz_files[0])
            logger.info(f"Found db.gz file: {db_gz_file}")
            
            # Decompress
            db_file = db_gz_file[:-3]  # Remove .gz extension
            
            with gzip.open(db_gz_file, 'rb') as f_in:
                with open(db_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"db.gz decompressed to {db_file}")
            return db_file
            
        except Exception as e:
            logger.error(f"Database decompression failed: {str(e)}")
            return None
    
    @log_execution_time
    def convert_bson_to_json(self, bson_file: str, json_file: str) -> bool:
        """Convert BSON database file to JSON"""
        try:
            # Use bsondump to convert BSON to JSON
            cmd = ['bsondump', bson_file]
            
            with open(json_file, 'w') as output_file:
                result = subprocess.run(cmd, stdout=output_file, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                logger.error(f"bsondump failed: {result.stderr}")
                return False
            
            logger.info(f"BSON converted to JSON: {json_file}")
            return True
            
        except Exception as e:
            logger.error(f"BSON to JSON conversion failed: {str(e)}")
            return False
    
    @log_execution_time
    def split_json_documents(self, json_file: str, output_dir: str) -> List[str]:
        """Split JSON file into individual documents"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            document_files = []
            
            with open(json_file, 'r') as f:
                doc_number = 1
                for line in f:
                    if line.strip():  # Skip empty lines
                        try:
                            # Validate JSON
                            json.loads(line)
                            
                            doc_filename = f"doc-{doc_number:06d}.json"
                            doc_path = os.path.join(output_dir, doc_filename)
                            
                            with open(doc_path, 'w') as doc_file:
                                doc_file.write(line)
                            
                            document_files.append(doc_path)
                            doc_number += 1
                            
                        except json.JSONDecodeError:
                            logger.warning(f"Skipping invalid JSON line {doc_number}")
                            continue
            
            logger.info(f"Split {len(document_files)} JSON documents to {output_dir}")
            return document_files
            
        except Exception as e:
            logger.error(f"JSON splitting failed: {str(e)}")
            return []
    
    @log_execution_time
    def process_backup(self) -> Optional[Dict]:
        """Complete backup processing pipeline"""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        output_folder = os.path.join(self.config.OUTPUT_DIR, f"unifi-backup-{timestamp}")
        os.makedirs(output_folder, exist_ok=True)
        
        try:
            # Step 1: Get latest backup file
            remote_backup = self.get_latest_backup_file()
            if not remote_backup:
                return None
            
            # Step 2: Download backup file
            local_backup = os.path.join(output_folder, os.path.basename(remote_backup))
            if not self.download_backup_file(remote_backup, local_backup):
                return None
            
            # Step 3: Decrypt .unf file
            decrypted_zip = os.path.join(output_folder, "decrypted.zip")
            if not self.decrypt_unf_file(local_backup, decrypted_zip):
                return None
            
            # Step 4: Extract ZIP
            extract_dir = os.path.join(output_folder, "extracted")
            if not self.extract_zip_file(decrypted_zip, extract_dir):
                return None
            
            # Step 5: Decompress database
            db_file = self.find_and_decompress_db(extract_dir)
            if not db_file:
                return None
            
            # Step 6: Convert BSON to JSON
            json_file = os.path.join(output_folder, "db.json")
            if not self.convert_bson_to_json(db_file, json_file):
                return None
            
            # Step 7: Split into individual documents
            json_docs_dir = os.path.join(output_folder, "json_documents")
            document_files = self.split_json_documents(json_file, json_docs_dir)
            
            if not document_files:
                return None
            
            logger.info("UniFi backup processing completed successfully")
            
            return {
                'output_folder': output_folder,
                'json_file': json_file,
                'document_files': document_files,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Backup processing failed: {str(e)}")
            return None