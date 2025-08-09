#!/usr/bin/env python3
"""
UniFi backup decryption utility.
Decrypts .unf backup files from UniFi controllers.
"""

import os
import sys
import hashlib
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UniFiBackupDecryptor:
    """Handles decryption of UniFi .unf backup files."""
    
    # Default decryption key for UniFi backups
    DEFAULT_KEY = b"ubntenterpriseappinc"
    
    def __init__(self, key=None):
        """Initialize decryptor with optional custom key."""
        self.key = key or self.DEFAULT_KEY
        
    def decrypt_backup(self, input_file, output_file=None):
        """
        Decrypt a UniFi .unf backup file.
        
        Args:
            input_file (str): Path to encrypted .unf file
            output_file (str): Path for decrypted output (optional)
            
        Returns:
            str: Path to decrypted file
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
            
        if not output_file:
            output_file = input_file.replace('.unf', '.tar.gz')
            
        logger.info(f"Decrypting {input_file} to {output_file}")
        
        try:
            with open(input_file, 'rb') as infile:
                # Read the encrypted data
                encrypted_data = infile.read()
                
            # Decrypt the data
            decrypted_data = self._decrypt_data(encrypted_data)
            
            # Write decrypted data
            with open(output_file, 'wb') as outfile:
                outfile.write(decrypted_data)
                
            logger.info(f"Successfully decrypted to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to decrypt backup: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data):
        """
        Decrypt the encrypted backup data using AES-128-CBC.
        
        Args:
            encrypted_data (bytes): The encrypted data
            
        Returns:
            bytes: Decrypted data
        """
        if len(encrypted_data) < 16:
            raise ValueError("Encrypted data too short")
            
        # Extract IV (first 16 bytes)
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Create cipher
        key_hash = hashlib.md5(self.key).digest()
        cipher = Cipher(
            algorithms.AES(key_hash),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        # Decrypt
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove PKCS7 padding
        padding_length = decrypted[-1]
        if padding_length > 16:
            raise ValueError("Invalid padding")
            
        decrypted = decrypted[:-padding_length]
        
        return decrypted
    
    def verify_backup(self, file_path):
        """
        Verify if a file is a valid UniFi backup.
        
        Args:
            file_path (str): Path to the backup file
            
        Returns:
            bool: True if valid backup
        """
        try:
            with open(file_path, 'rb') as f:
                # Check file size
                f.seek(0, 2)  # Seek to end
                size = f.tell()
                if size < 32:  # Minimum size check
                    return False
                    
                f.seek(0)  # Reset to beginning
                header = f.read(32)
                
                # Basic validation - check if it looks like encrypted data
                return len(header) == 32
                
        except Exception:
            return False

def main():
    """Command line interface for backup decryption."""
    if len(sys.argv) < 2:
        print("Usage: python decrypt_backup.py <input.unf> [output.tar.gz]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        decryptor = UniFiBackupDecryptor()
        
        # Verify backup first
        if not decryptor.verify_backup(input_file):
            logger.warning("Warning: File may not be a valid UniFi backup")
            
        # Decrypt
        result = decryptor.decrypt_backup(input_file, output_file)
        print(f"Decryption successful: {result}")
        
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()