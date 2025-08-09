#!/usr/bin/env python3
"""
Backup to JSON conversion utilities for Unifi backup files.
Handles decryption of .unf files and conversion to structured JSON format.
"""

import base64
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import py7zr
import structlog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class BackupJsonConverter:
    """Converts Unifi backup files to structured JSON format."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the JSON converter with configuration."""
        self.config = config
        self.logger = structlog.get_logger("json_converter")

    def _decrypt_unf_file(
        self, unf_file_path: Path, output_dir: Path
    ) -> Optional[Path]:
        """Decrypt a .unf backup file to extract the archive contents."""
        try:
            self.logger.info("Decrypting .unf backup file", file=str(unf_file_path))

            # Read the .unf file
            with open(unf_file_path, "rb") as f:
                encrypted_data = f.read()

            # Unifi backup files are typically encrypted with a known key or are actually
            # just renamed zip/7z files. Let's try different approaches:

            # First, try to treat it as a regular zip file (sometimes .unf files are just renamed zips)
            try:
                with zipfile.ZipFile(unf_file_path, "r") as zip_ref:
                    zip_ref.extractall(output_dir)
                    self.logger.info("Successfully extracted as ZIP file")
                    return output_dir
            except zipfile.BadZipFile:
                pass

            # Try to treat it as a 7z file
            try:
                with py7zr.SevenZipFile(unf_file_path, mode="r") as archive:
                    archive.extractall(output_dir)
                    self.logger.info("Successfully extracted as 7Z file")
                    return output_dir
            except:
                pass

            # If it's actually encrypted, we need to try known Unifi encryption methods
            # Many Unifi controllers use a default encryption or no encryption at all

            # Try common Unifi decryption methods
            decryption_keys = [
                b"ubnt",  # Default Ubiquiti key
                b"unifi",  # Common Unifi key
                b"default",  # Default key
                self.config.get("unifi_password", "").encode(),  # Use SSH password
            ]

            for key in decryption_keys:
                try:
                    decrypted_data = self._try_decrypt_with_key(encrypted_data, key)
                    if decrypted_data:
                        # Write decrypted data to a temporary file and try to extract
                        temp_file = output_dir / "decrypted.zip"
                        with open(temp_file, "wb") as f:
                            f.write(decrypted_data)

                        try:
                            with zipfile.ZipFile(temp_file, "r") as zip_ref:
                                zip_ref.extractall(output_dir)
                                temp_file.unlink()  # Remove temporary file
                                self.logger.info("Successfully decrypted and extracted")
                                return output_dir
                        except zipfile.BadZipFile:
                            pass

                        temp_file.unlink()  # Clean up
                except Exception:
                    continue

            # If all decryption attempts fail, copy the original file and let the user know
            self.logger.warning(
                "Could not decrypt .unf file, copying as-is for manual processing"
            )
            copied_file = output_dir / unf_file_path.name
            shutil.copy2(unf_file_path, copied_file)
            return output_dir

        except Exception as e:
            self.logger.error("Error decrypting .unf file", error=str(e), exc_info=True)
            return None

    def _try_decrypt_with_key(
        self, encrypted_data: bytes, key: bytes
    ) -> Optional[bytes]:
        """Try to decrypt data with a given key using various methods."""
        try:
            # Method 1: Simple XOR (sometimes used by Ubiquiti)
            if len(key) > 0:
                xor_result = bytearray()
                for i, byte in enumerate(encrypted_data):
                    xor_result.append(byte ^ key[i % len(key)])

                # Check if result looks like a zip file
                if xor_result[:4] == b"PK\x03\x04":
                    return bytes(xor_result)

            # Method 2: PBKDF2 + Fernet (modern encryption)
            try:
                salt = encrypted_data[:16]  # Assume first 16 bytes are salt
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                derived_key = base64.urlsafe_b64encode(kdf.derive(key))
                fernet = Fernet(derived_key)
                decrypted = fernet.decrypt(encrypted_data[16:])
                return decrypted
            except Exception:
                pass

            # Method 3: Direct key usage (if it's base64 encoded)
            try:
                if len(key) == 32 or len(key) == 44:  # Potential Fernet key
                    if len(key) == 32:
                        fernet_key = base64.urlsafe_b64encode(key)
                    else:
                        fernet_key = key
                    fernet = Fernet(fernet_key)
                    decrypted = fernet.decrypt(encrypted_data)
                    return decrypted
            except Exception:
                pass

        except Exception:
            pass

        return None

    def _extract_archive_contents(self, archive_path: Path, output_dir: Path) -> bool:
        """Extract contents from various archive formats."""
        try:
            # Try ZIP first
            if zipfile.is_zipfile(archive_path):
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    zip_ref.extractall(output_dir)
                return True

            # Try 7Z
            try:
                with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                    archive.extractall(output_dir)
                return True
            except:
                pass

            return False

        except Exception as e:
            self.logger.error("Error extracting archive", error=str(e))
            return False

    def _process_json_files(self, extracted_dir: Path) -> Dict[str, Any]:
        """Process extracted JSON files and organize them into structured data."""
        json_data = {}

        try:
            # Find all JSON files in the extracted directory
            json_files = list(extracted_dir.rglob("*.json"))

            self.logger.info("Processing JSON files", count=len(json_files))

            for json_file in json_files:
                try:
                    relative_path = json_file.relative_to(extracted_dir)

                    with open(json_file, "r", encoding="utf-8") as f:
                        file_data = json.load(f)

                    # Organize data by file type/category
                    file_key = str(relative_path).replace("/", "_").replace(".json", "")
                    json_data[file_key] = file_data

                    self.logger.debug("Processed JSON file", file=str(relative_path))

                except Exception as e:
                    self.logger.warning(
                        "Error processing JSON file", file=str(json_file), error=str(e)
                    )

        except Exception as e:
            self.logger.error("Error processing JSON files", error=str(e))

        return json_data

    def _process_binary_files(self, extracted_dir: Path) -> Dict[str, Any]:
        """Process binary configuration files and convert them to readable format."""
        binary_data = {}

        try:
            # Look for common Unifi binary configuration files
            binary_patterns = ["*.cfg", "*.conf", "*.db", "*.properties"]

            for pattern in binary_patterns:
                for binary_file in extracted_dir.rglob(pattern):
                    try:
                        relative_path = binary_file.relative_to(extracted_dir)
                        file_key = str(relative_path).replace("/", "_")

                        # Try to read as text first
                        try:
                            with open(binary_file, "r", encoding="utf-8") as f:
                                content = f.read()
                            binary_data[file_key] = {"type": "text", "content": content}
                        except UnicodeDecodeError:
                            # If not text, store file metadata
                            stat = binary_file.stat()
                            binary_data[file_key] = {
                                "type": "binary",
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(
                                    stat.st_mtime
                                ).isoformat(),
                                "path": str(relative_path),
                            }

                        self.logger.debug(
                            "Processed binary file", file=str(relative_path)
                        )

                    except Exception as e:
                        self.logger.warning(
                            "Error processing binary file",
                            file=str(binary_file),
                            error=str(e),
                        )

        except Exception as e:
            self.logger.error("Error processing binary files", error=str(e))

        return binary_data

    def _create_structured_output(
        self,
        json_data: Dict[str, Any],
        binary_data: Dict[str, Any],
        backup_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a structured output with all backup data organized by category."""

        structured_data = {
            "backup_metadata": {
                "timestamp": datetime.now().isoformat(),
                "source_file": backup_info.get("source_file", ""),
                "controller_host": self.config.get("unifi_host", ""),
                "extraction_method": backup_info.get("extraction_method", "unknown"),
                "total_files": backup_info.get("total_files", 0),
            },
            "sites": {},
            "devices": {},
            "networks": {},
            "users": {},
            "settings": {},
            "other": {},
        }

        # Categorize JSON data
        for key, data in json_data.items():
            if isinstance(data, list):
                # Handle list data (often device or user collections)
                if "device" in key.lower():
                    structured_data["devices"][key] = data
                elif "user" in key.lower() or "client" in key.lower():
                    structured_data["users"][key] = data
                elif "site" in key.lower():
                    structured_data["sites"][key] = data
                elif "network" in key.lower() or "wlan" in key.lower():
                    structured_data["networks"][key] = data
                else:
                    structured_data["other"][key] = data
            elif isinstance(data, dict):
                # Handle dictionary data (often settings or configurations)
                if "setting" in key.lower() or "config" in key.lower():
                    structured_data["settings"][key] = data
                elif "site" in key.lower():
                    structured_data["sites"][key] = data
                elif "device" in key.lower():
                    structured_data["devices"][key] = data
                elif "network" in key.lower() or "wlan" in key.lower():
                    structured_data["networks"][key] = data
                else:
                    structured_data["other"][key] = data
            else:
                structured_data["other"][key] = data

        # Add binary data
        if binary_data:
            structured_data["binary_files"] = binary_data

        return structured_data

    def convert_backup(self, backup_file_path: Path) -> List[Path]:
        """Convert a Unifi backup file to structured JSON format."""
        try:
            self.logger.info("Starting backup conversion", file=str(backup_file_path))

            # Create output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_base_dir = backup_file_path.parent / f"json_{timestamp}"
            output_base_dir.mkdir(exist_ok=True)

            # Create temporary extraction directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Extract/decrypt the backup file
                if backup_file_path.suffix.lower() == ".unf":
                    extracted_dir = self._decrypt_unf_file(backup_file_path, temp_path)
                else:
                    extracted_dir = temp_path
                    success = self._extract_archive_contents(
                        backup_file_path, extracted_dir
                    )
                    if not success:
                        # If extraction fails, just copy the file
                        shutil.copy2(
                            backup_file_path, temp_path / backup_file_path.name
                        )

                if not extracted_dir:
                    self.logger.error("Failed to extract backup file")
                    return []

                # Process extracted files
                json_data = self._process_json_files(extracted_dir)
                binary_data = self._process_binary_files(extracted_dir)

                # Count total files
                total_files = len(list(extracted_dir.rglob("*")))

                backup_info = {
                    "source_file": str(backup_file_path),
                    "extraction_method": (
                        "unf_decrypt"
                        if backup_file_path.suffix.lower() == ".unf"
                        else "archive_extract"
                    ),
                    "total_files": total_files,
                }

                # Create structured output
                structured_data = self._create_structured_output(
                    json_data, binary_data, backup_info
                )

                # Write individual category files
                output_files = []

                for category, data in structured_data.items():
                    if data and category != "backup_metadata":
                        category_file = output_base_dir / f"{category}.json"
                        with open(category_file, "w", encoding="utf-8") as f:
                            json.dump(
                                data, f, indent=2, default=str, ensure_ascii=False
                            )
                        output_files.append(category_file)
                        self.logger.debug(
                            "Created category file",
                            category=category,
                            file=str(category_file),
                        )

                # Write complete structured data
                complete_file = output_base_dir / "complete_backup.json"
                with open(complete_file, "w", encoding="utf-8") as f:
                    json.dump(
                        structured_data, f, indent=2, default=str, ensure_ascii=False
                    )
                output_files.append(complete_file)

                # Write summary
                summary_file = output_base_dir / "summary.json"
                summary = {
                    "conversion_timestamp": datetime.now().isoformat(),
                    "source_backup": str(backup_file_path),
                    "categories": {
                        category: len(data) if isinstance(data, (dict, list)) else 1
                        for category, data in structured_data.items()
                        if data and category != "backup_metadata"
                    },
                    "total_output_files": len(output_files),
                    "backup_metadata": structured_data["backup_metadata"],
                }

                with open(summary_file, "w", encoding="utf-8") as f:
                    json.dump(summary, f, indent=2, default=str, ensure_ascii=False)
                output_files.append(summary_file)

                self.logger.info(
                    "Backup conversion completed successfully",
                    output_dir=str(output_base_dir),
                    output_files=len(output_files),
                    categories=len(
                        [
                            k
                            for k, v in structured_data.items()
                            if v and k != "backup_metadata"
                        ]
                    ),
                )

                return output_files

        except Exception as e:
            self.logger.error("Error converting backup", error=str(e), exc_info=True)
            return []

    def validate_json_output(self, json_files: List[Path]) -> Dict[str, Any]:
        """Validate the generated JSON files for correctness."""
        validation_results = {
            "valid_files": 0,
            "invalid_files": 0,
            "total_size": 0,
            "errors": [],
        }

        try:
            for json_file in json_files:
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        json.load(f)  # Just validate it's valid JSON

                    validation_results["valid_files"] += 1
                    validation_results["total_size"] += json_file.stat().st_size

                except json.JSONDecodeError as e:
                    validation_results["invalid_files"] += 1
                    validation_results["errors"].append(
                        {
                            "file": str(json_file),
                            "error": f"JSON decode error: {str(e)}",
                        }
                    )
                except Exception as e:
                    validation_results["invalid_files"] += 1
                    validation_results["errors"].append(
                        {"file": str(json_file), "error": str(e)}
                    )

        except Exception as e:
            validation_results["errors"].append({"general": str(e)})

        return validation_results
