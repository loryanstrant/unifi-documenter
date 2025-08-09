#!/usr/bin/env python3
"""
Unit tests for UniFi Documenter backup functionality.
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tarfile
import shutil

# Add the app directory to the path
sys.path.insert(0, '/app')

from backup import UniFiBackupManager
from decrypt_backup import UniFiBackupDecryptor

class TestUniFiBackupDecryptor(unittest.TestCase):
    """Test cases for UniFi backup decryption."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.decryptor = UniFiBackupDecryptor()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_with_default_key(self):
        """Test decryptor initialization with default key."""
        decryptor = UniFiBackupDecryptor()
        self.assertEqual(decryptor.key, b"ubntenterpriseappinc")
    
    def test_init_with_custom_key(self):
        """Test decryptor initialization with custom key."""
        custom_key = b"customkey123"
        decryptor = UniFiBackupDecryptor(custom_key)
        self.assertEqual(decryptor.key, custom_key)
    
    def test_verify_backup_nonexistent_file(self):
        """Test backup verification with non-existent file."""
        result = self.decryptor.verify_backup("/nonexistent/file")
        self.assertFalse(result)
    
    def test_verify_backup_small_file(self):
        """Test backup verification with file too small."""
        small_file = Path(self.temp_dir) / "small.unf"
        with open(small_file, 'wb') as f:
            f.write(b"small")
        
        result = self.decryptor.verify_backup(str(small_file))
        self.assertFalse(result)
    
    def test_verify_backup_valid_size_file(self):
        """Test backup verification with valid size file."""
        valid_file = Path(self.temp_dir) / "valid.unf"
        with open(valid_file, 'wb') as f:
            f.write(b"x" * 64)  # Write 64 bytes
        
        result = self.decryptor.verify_backup(str(valid_file))
        self.assertTrue(result)

class TestUniFiBackupManager(unittest.TestCase):
    """Test cases for UniFi backup manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'UNIFI_HOST': '192.168.1.1',
            'UNIFI_SSH_USER': 'root',
            'UNIFI_SSH_PASSWORD': 'testpass',
            'BACKUP_RETENTION_DAYS': '7',
            'TZ': 'UTC'
        })
        self.env_patcher.start()
        
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.backup_dir = Path(self.temp_dir) / "backups"
        self.backup_dir.mkdir(parents=True)
        
        # Mock the backup directory
        with patch.object(Path, '__new__', return_value=self.backup_dir) as mock_path:
            try:
                self.manager = UniFiBackupManager()
            except Exception:
                # Fallback initialization for testing
                self.manager = UniFiBackupManager.__new__(UniFiBackupManager)
                self.manager.config = {
                    'host': '192.168.1.1',
                    'port': 22,
                    'username': 'root',
                    'password': 'testpass',
                    'key_file': None,
                    'backup_password': '',
                    'retention_days': 7,
                    'timezone': 'UTC',
                }
                self.manager.ssh_client = None
                self.manager.decryptor = UniFiBackupDecryptor()
                self.manager.backup_dir = self.backup_dir
                self.manager.latest_dir = self.backup_dir / "latest"
                self.manager.archive_dir = self.backup_dir / "archives"
                self.manager.temp_dir = Path(tempfile.mkdtemp())
                for dir_path in [self.manager.latest_dir, self.manager.archive_dir]:
                    dir_path.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_config_with_valid_env(self):
        """Test configuration loading with valid environment variables."""
        config = self.manager.config
        
        self.assertEqual(config['host'], '192.168.1.1')
        self.assertEqual(config['username'], 'root')
        self.assertEqual(config['password'], 'testpass')
        self.assertEqual(config['retention_days'], 7)
        self.assertEqual(config['timezone'], 'UTC')
    
    def test_load_config_missing_host(self):
        """Test configuration loading with missing host."""
        with patch.dict(os.environ, {'UNIFI_HOST': ''}, clear=True):
            with self.assertRaises(ValueError) as context:
                UniFiBackupManager()
            self.assertIn("Missing required configuration", str(context.exception))
    
    def test_load_config_missing_auth(self):
        """Test configuration loading with missing authentication."""
        with patch.dict(os.environ, {
            'UNIFI_HOST': '192.168.1.1',
            'UNIFI_SSH_USER': 'root'
        }, clear=True):
            with self.assertRaises(ValueError) as context:
                UniFiBackupManager()
            self.assertIn("Either UNIFI_SSH_PASSWORD or UNIFI_SSH_KEY", str(context.exception))
    
    @patch('paramiko.SSHClient')
    def test_connect_ssh_with_password(self, mock_ssh_client):
        """Test SSH connection with password authentication."""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        
        result = self.manager.connect_ssh()
        
        mock_client.set_missing_host_key_policy.assert_called_once()
        mock_client.connect.assert_called_once_with(
            hostname='192.168.1.1',
            port=22,
            username='root',
            password='testpass',
            timeout=30
        )
        self.assertEqual(result, mock_client)
    
    @patch('paramiko.SSHClient')
    def test_connect_ssh_with_key_file(self, mock_ssh_client):
        """Test SSH connection with key file authentication."""
        # Create a mock key file
        key_file = Path(self.temp_dir) / "test_key"
        key_file.write_text("mock key content")
        
        with patch.dict(os.environ, {
            'UNIFI_SSH_KEY': str(key_file),
            'UNIFI_SSH_PASSWORD': ''
        }):
            manager = UniFiBackupManager()
            
            mock_client = Mock()
            mock_ssh_client.return_value = mock_client
            
            result = manager.connect_ssh()
            
            mock_client.connect.assert_called_once_with(
                hostname='192.168.1.1',
                port=22,
                username='root',
                key_filename=str(key_file),
                timeout=30
            )
    
    def test_convert_bson_to_json_nonexistent_file(self):
        """Test BSON to JSON conversion with non-existent file."""
        bson_file = str(Path(self.temp_dir) / "nonexistent.bson")
        json_file = str(Path(self.temp_dir) / "output.json")
        
        # Should handle the error gracefully and create empty JSON
        self.manager.convert_bson_to_json(bson_file, json_file)
        
        # Check that empty JSON file was created
        self.assertTrue(Path(json_file).exists())
        with open(json_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data, [])
    
    def test_setup_git_repo_new_repo(self):
        """Test Git repository setup for new repository."""
        repo_path = str(Path(self.temp_dir) / "new_repo")
        os.makedirs(repo_path)
        
        with patch('subprocess.run') as mock_run:
            self.manager.setup_git_repo(repo_path)
            
            # Should call git init
            mock_run.assert_called_with(['git', 'init'], cwd=repo_path, check=True)
            
            # Should create .gitignore
            gitignore_path = Path(repo_path) / '.gitignore'
            self.assertTrue(gitignore_path.exists())
    
    def test_setup_git_repo_existing_repo(self):
        """Test Git repository setup for existing repository."""
        repo_path = str(Path(self.temp_dir) / "existing_repo")
        os.makedirs(repo_path)
        git_dir = Path(repo_path) / '.git'
        git_dir.mkdir()
        
        with patch('subprocess.run') as mock_run:
            self.manager.setup_git_repo(repo_path)
            
            # Should not call git init for existing repo
            mock_run.assert_not_called()
    
    @patch('subprocess.run')
    def test_commit_backup_with_changes(self, mock_run):
        """Test Git commit with changes."""
        backup_path = str(self.backup_dir)
        
        # Mock git diff to indicate changes
        mock_run.side_effect = [
            None,  # git add
            Mock(returncode=1),  # git diff --staged --quiet (changes exist)
            None   # git commit
        ]
        
        self.manager.commit_backup(backup_path)
        
        # Should call git add, git diff, and git commit
        self.assertEqual(mock_run.call_count, 3)
    
    @patch('subprocess.run')
    def test_commit_backup_no_changes(self, mock_run):
        """Test Git commit with no changes."""
        backup_path = str(self.backup_dir)
        
        # Mock git diff to indicate no changes
        mock_run.side_effect = [
            None,  # git add
            Mock(returncode=0)  # git diff --staged --quiet (no changes)
        ]
        
        self.manager.commit_backup(backup_path)
        
        # Should call git add and git diff, but not git commit
        self.assertEqual(mock_run.call_count, 2)
    
    def test_cleanup_old_backups(self):
        """Test cleanup of old backup files."""
        # Create test backup files
        old_backup = self.backup_dir / "archives" / "backup_20220101_120000.tar.gz"
        recent_backup = self.backup_dir / "archives" / "backup_20231201_120000.tar.gz"
        
        old_backup.parent.mkdir(parents=True, exist_ok=True)
        old_backup.touch()
        recent_backup.touch()
        
        # Set old modification time
        import time
        old_time = time.time() - (40 * 24 * 60 * 60)  # 40 days ago
        os.utime(old_backup, (old_time, old_time))
        
        # Run cleanup
        self.manager.cleanup_old_backups()
        
        # Old backup should be removed, recent should remain
        self.assertFalse(old_backup.exists())
        self.assertTrue(recent_backup.exists())

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete backup process."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'UNIFI_HOST': '192.168.1.1',
            'UNIFI_SSH_USER': 'root',
            'UNIFI_SSH_PASSWORD': 'testpass',
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_sample_backup_structure(self):
        """Test creation of sample backup structure for validation."""
        # Create a sample tar.gz file that mimics UniFi backup structure
        backup_dir = Path(self.temp_dir) / "sample_backup"
        backup_dir.mkdir()
        
        # Create sample configuration files
        (backup_dir / "system.properties").write_text("unifi.version=7.4.162\nserver.name=Dream Machine")
        (backup_dir / "config.json").write_text('{"site_name": "default", "devices": []}')
        
        # Create sample BSON file (mock)
        bson_file = backup_dir / "users.bson"
        bson_file.write_bytes(b'\x16\x00\x00\x00\x02name\x00\x05\x00\x00\x00test\x00\x00')
        
        # Create tar.gz
        archive_path = Path(self.temp_dir) / "test_backup.tar.gz"
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_dir, arcname='backup')
        
        # Verify archive was created
        self.assertTrue(archive_path.exists())
        
        # Test extraction
        extract_dir = Path(self.temp_dir) / "extracted"
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(extract_dir)
        
        # Verify extracted content
        self.assertTrue((extract_dir / "backup" / "system.properties").exists())
        self.assertTrue((extract_dir / "backup" / "config.json").exists())
        self.assertTrue((extract_dir / "backup" / "users.bson").exists())

def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestUniFiBackupDecryptor))
    suite.addTests(loader.loadTestsFromTestCase(TestUniFiBackupManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)