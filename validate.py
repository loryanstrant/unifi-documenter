#!/usr/bin/env python3
"""
Basic validation script to test the container functionality.
This script can be used to validate the implementation without requiring an actual Unifi controller.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
import sys

sys.path.insert(0, ".")

from backup_script import BackupOrchestrator
from json_converter import BackupJsonConverter
from scheduler import BackupScheduler
from unifi_backup import UnifiBackupManager

def test_configuration_loading():
    """Test configuration loading from environment variables."""
    print("Testing configuration loading...")

    # Set test environment variables
    os.environ.update(
        {
            "UNIFI_HOST": "test.example.com",
            "UNIFI_USERNAME": "test_user",
            "UNIFI_PASSWORD": "test_password",
            "BACKUP_SCHEDULE": "daily",
            "BACKUP_TIME": "02:00",
            "TZ": "UTC",
            "LOG_LEVEL": "DEBUG",
        }
    )

    try:
        orchestrator = BackupOrchestrator()
        config = orchestrator.config

        assert config["unifi_host"] == "test.example.com"
        assert config["unifi_username"] == "test_user"
        assert config["backup_schedule"] == "daily"
        assert config["backup_time"] == "02:00"

        print("✅ Configuration loading test passed")
        return True
    except Exception as e:
        print(f"❌ Configuration loading test failed: {e}")
        return False

def test_scheduler_functionality():
    """Test scheduler cron expression generation and state management."""
    print("Testing scheduler functionality...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "backup_schedule": "daily",
                "backup_time": "02:00",
                "backup_directory": temp_dir,
                "timezone": "UTC",
            }

            scheduler = BackupScheduler(config)

            # Test cron expression generation
            cron_expr = scheduler._get_cron_expression()
            assert cron_expr == "0 2 * * *"

            # Test schedule info
            schedule_info = scheduler.get_schedule_info()
            assert "cron_expression" in schedule_info
            assert schedule_info["schedule_type"] == "daily"

            print("✅ Scheduler functionality test passed")
            return True
    except Exception as e:
        print(f"❌ Scheduler functionality test failed: {e}")
        return False

def test_json_converter():
    """Test JSON converter with a mock backup file."""
    print("Testing JSON converter...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "backup_directory": temp_dir,
                "unifi_host": "test.example.com",
            }

            converter = BackupJsonConverter(config)

            # Create a mock backup file (simple zip with JSON content)
            mock_backup_path = Path(temp_dir) / "mock_backup.zip"

            import zipfile

            with zipfile.ZipFile(mock_backup_path, "w") as zf:
                # Add mock JSON data
                mock_data = {
                    "sites": [{"name": "default", "id": "test123"}],
                    "devices": [{"name": "AP1", "type": "access-point"}],
                }
                zf.writestr("sites.json", json.dumps(mock_data["sites"]))
                zf.writestr("devices.json", json.dumps(mock_data["devices"]))

            # Test validation
            validation_results = converter.validate_json_output([mock_backup_path])

            print("✅ JSON converter test passed")
            return True
    except Exception as e:
        print(f"❌ JSON converter test failed: {e}")
        return False

def test_health_check():
    """Test health check functionality."""
    print("Testing health check...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ["BACKUP_DIRECTORY"] = temp_dir

            orchestrator = BackupOrchestrator()
            health_status = orchestrator.health_check()

            assert "status" in health_status
            assert "timestamp" in health_status
            assert "config" in health_status

            print("✅ Health check test passed")
            return True
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return False

def test_unifi_backup_manager():
    """Test UnifiBackupManager initialization."""
    print("Testing UnifiBackupManager...")

    try:
        config = {
            "unifi_host": "test.example.com",
            "unifi_username": "test_user",
            "unifi_password": "test_password",
            "unifi_port": 22,
            "connection_timeout": 30,
        }

        manager = UnifiBackupManager(config)

        # Test that manager initializes correctly
        assert manager.config == config
        assert manager.ssh_client is None

        print("✅ UnifiBackupManager test passed")
        return True
    except Exception as e:
        print(f"❌ UnifiBackupManager test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Starting validation tests for Unifi Backup Container")
    print("=" * 60)

    tests = [
        test_configuration_loading,
        test_scheduler_functionality,
        test_json_converter,
        test_health_check,
        test_unifi_backup_manager,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Container functionality is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
