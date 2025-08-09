#!/usr/bin/env python3
"""
Basic validation script to test the container functionality.
This script can be used to validate the implementation without
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
import sys
sys.path.insert(0, '.')

from backup_script import BackupOrchestrator
from json_converter import BackupJsonConverter
from scheduler import BackupScheduler
from unifi_backup import UnifiBackupManager

def test_configuration_loading():
    """Test configuration loading from environment variables."""
    print("Testing configuration loading...")
    # Set test environment variables
    os.environ.update({
        'UNIFI_HOST': 'test.example.com',
        'UNIFI_USERNAME': 'test_user',
        'UNIFI_PASSWORD': 'test_password',
        'BACKUP_SCHEDULE': 'daily',
        'BACKUP_TIME': '02:00',
        'TZ': 'UTC',
        'LOG_LEVEL': 'DEBUG'
    })
    try:
        orchestrator = BackupOrchestrator()
        config = orchestrator.config
        assert config['unifi_host'] == 'test.example.com'
        assert config['unifi_username'] == 'test_user'
        assert config['backup_schedule'] == 'daily'
        assert config['backup_time'] == '02:00'
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
                'backup_schedule': 'daily',
                'backup_time': '02:00',
                'backup_directory': temp_dir,
                'timezone': 'UTC'
            }
            scheduler = BackupScheduler(config)
            # Test cron expression generation
            cron_expr = scheduler._get_cron_expression()
            assert cron_expr == "0 2 * * *"
            # Test schedule info
            schedule_info = scheduler.get_schedule_info()
            assert 'cron_expression' in schedule_info
            assert schedule_info['schedule_type'] == 'daily'
            print("✅ Scheduler functionality test passed")
            return True
    except Exception as e:
        print(f"❌ Scheduler functionality test failed: {e}")
        return False

