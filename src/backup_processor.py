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

# Handle relative imports for when module is run standalone
try:
    from .utils import log_execution_time
    from .config import Config
except ImportError:
    from utils import log_execution_time
    from config import Config

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
        auth_methods_tried = []
        
        try:
            # First, try standard password authentication (simplest)
            try:
                logger.info("Attempting password authentication...")
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                self.ssh_client.connect(
                    hostname=self.config.UDM_IP,
                    username='root',
                    password=self.config.UDM_ROOT_PASSWORD,
                    timeout=10,  # Reduced timeout for faster testing
                    look_for_keys=False,
                    allow_agent=False,
                    auth_timeout=10
                )
                logger.info(f"Successfully connected to UDM at {self.config.UDM_IP} using password authentication")
                return True
                
            except paramiko.AuthenticationException as pwd_e:
                auth_methods_tried.append(f"password: {str(pwd_e)}")
                logger.warning(f"Password authentication failed: {str(pwd_e)}")
                
                # If password auth failed, try keyboard-interactive
                try:
                    logger.info("Attempting keyboard-interactive authentication...")
                    self._connect_with_keyboard_interactive()
                    logger.info(f"Successfully connected to UDM at {self.config.UDM_IP} using keyboard-interactive authentication")
                    return True
                    
                except Exception as ki_e:
                    auth_methods_tried.append(f"keyboard-interactive: {str(ki_e)}")
                    logger.warning(f"Keyboard-interactive authentication failed: {str(ki_e)}")
                    
                    # Log all attempted methods for debugging
                    logger.error(f"All authentication methods failed. Attempted: {'; '.join(auth_methods_tried)}")
                    return False
            
        except Exception as e:
            logger.error(f"Failed to connect to UDM: {str(e)}")
            if auth_methods_tried:
                logger.error(f"Authentication methods tried: {'; '.join(auth_methods_tried)}")
            return False
    
    def _connect_with_keyboard_interactive(self):
        """Helper method to handle keyboard-interactive authentication"""
        # Create a new client for keyboard-interactive auth
        if self.ssh_client:
            self.ssh_client.close()
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            # First try: Standard connect which might negotiate keyboard-interactive
            self.ssh_client.connect(
                hostname=self.config.UDM_IP,
                username='root',
                password=self.config.UDM_ROOT_PASSWORD,
                timeout=10,  # Shorter timeout for faster failure
                auth_timeout=10,
                look_for_keys=False,
                allow_agent=False
            )
            
        except paramiko.AuthenticationException as e:
            # If that fails, try manual keyboard-interactive
            logger.debug(f"Standard connect failed, trying manual keyboard-interactive: {e}")
            self._manual_keyboard_interactive()
    
    def _manual_keyboard_interactive(self):
        """Fallback method for manual keyboard-interactive authentication"""
        import socket
        
        # Close existing client if any
        if self.ssh_client:
            self.ssh_client.close()
        
        sock = None
        transport = None
        
        try:
            # Create socket and transport with shorter timeouts
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # Shorter timeout
            sock.connect((self.config.UDM_IP, 22))
            
            transport = paramiko.Transport(sock)
            transport.start_client(timeout=10)  # Add timeout to start_client
            
            # Define authentication handler
            def auth_handler(title, instructions, prompt_list):
                """Handle keyboard-interactive prompts"""
                responses = []
                for prompt, echo in prompt_list:
                    # Look for password prompts (case insensitive)
                    prompt_lower = prompt.lower()
                    if 'password' in prompt_lower or 'passwd' in prompt_lower:
                        responses.append(self.config.UDM_ROOT_PASSWORD)
                    else:
                        # For unknown prompts, try password
                        responses.append(self.config.UDM_ROOT_PASSWORD)
                return responses
            
            # Attempt keyboard-interactive authentication
            transport.auth_interactive('root', auth_handler)
            
            # Verify authentication was successful
            if not transport.is_authenticated():
                raise paramiko.AuthenticationException("Manual keyboard-interactive authentication failed")
            
            # Create new SSH client and properly attach transport
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client._transport = transport
            
        except Exception as e:
            # Clean up resources on failure
            if transport:
                try:
                    transport.close()
                except:
                    pass
            elif sock and hasattr(sock, 'fileno') and sock.fileno() != -1:
                try:
                    sock.close()
                except:
                    pass
            raise e
    
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
            # Use Python's bson module to convert BSON to JSON
            import bson
            
            documents = []
            with open(bson_file, 'rb') as f:
                # Read the entire BSON file
                bson_data = f.read()
                
                # Parse BSON documents
                offset = 0
                while offset < len(bson_data):
                    try:
                        # Get document size (first 4 bytes, little-endian)
                        if offset + 4 > len(bson_data):
                            break
                            
                        doc_size = int.from_bytes(bson_data[offset:offset+4], byteorder='little')
                        if doc_size <= 0 or offset + doc_size > len(bson_data):
                            break
                            
                        # Extract document
                        doc_bytes = bson_data[offset:offset+doc_size]
                        
                        # Decode BSON document
                        try:
                            doc = bson.decode(doc_bytes)
                            documents.append(doc)
                        except Exception as e:
                            logger.warning(f"Failed to decode BSON document at offset {offset}: {str(e)}")
                        
                        offset += doc_size
                        
                    except Exception as e:
                        logger.warning(f"Error processing BSON at offset {offset}: {str(e)}")
                        break
            
            # Write JSON documents
            with open(json_file, 'w') as f:
                for doc in documents:
                    import json
                    # Convert ObjectId and other BSON types to strings
                    def convert_bson_types(obj):
                        if hasattr(obj, '__dict__'):
                            return str(obj)
                        return obj
                    
                    json_doc = json.dumps(doc, default=convert_bson_types, separators=(',', ':'))
                    f.write(json_doc + '\n')
            
            logger.info(f"BSON converted to JSON: {json_file} ({len(documents)} documents)")
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