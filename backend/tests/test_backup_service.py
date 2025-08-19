"""
Tests for backup service functionality
"""
import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from services.backup_service import BackupService
from models import db, User, Account, Transaction, TransactionStatus
from decimal import Decimal

class TestBackupService:
    """Test cases for BackupService"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, app):
        """Set up test environment"""
        with app.app_context():
            # Create test backup directory
            self.test_backup_dir = tempfile.mkdtemp()
            BackupService.BACKUP_DIR = self.test_backup_dir
            
            # Create test data
            self.test_user = User(
                id='test-user-1',
                microsoft_id='test-ms-id',
                email='test@example.com',
                name='Test User'
            )
            db.session.add(self.test_user)
            
            self.test_account = Account(
                id='test-account-1',
                user_id=self.test_user.id,
                balance=Decimal('100.00')
            )
            db.session.add(self.test_account)
            
            self.test_transaction = Transaction(
                id='test-transaction-1',
                sender_id=self.test_user.id,
                recipient_id=self.test_user.id,
                amount=Decimal('50.00'),
                status=TransactionStatus.COMPLETED
            )
            db.session.add(self.test_transaction)
            
            db.session.commit()
            
            yield
            
            # Cleanup
            shutil.rmtree(self.test_backup_dir, ignore_errors=True)
    
    def test_create_database_backup(self, app):
        """Test database backup creation"""
        with app.app_context():
            result = BackupService.create_database_backup("test_backup")
            
            assert result['success'] is True
            assert 'backup_info' in result
            
            backup_info = result['backup_info']
            assert 'backup_id' in backup_info
            assert 'filename' in backup_info
            assert backup_info['encrypted'] is True
            assert backup_info['compressed'] is True
            assert backup_info['backup_type'] == 'full'
            
            # Check that backup file exists
            backup_path = Path(self.test_backup_dir) / backup_info['filename']
            assert backup_path.exists()
            assert backup_path.stat().st_size > 0
    
    def test_list_backups(self, app):
        """Test backup listing"""
        with app.app_context():
            # Create a backup first
            BackupService.create_database_backup("test_backup_1")
            BackupService.create_database_backup("test_backup_2")
            
            backups = BackupService.list_backups()
            
            assert len(backups) >= 2
            
            for backup in backups:
                assert 'backup_id' in backup
                assert 'filename' in backup
                assert 'created_at' in backup
                assert 'size_mb' in backup
                assert 'encrypted' in backup
                assert 'file_exists' in backup
    
    def test_backup_verification(self, app):
        """Test backup integrity verification"""
        with app.app_context():
            # Create a backup
            result = BackupService.create_database_backup("test_verification")
            assert result['success'] is True
            
            backup_id = result['backup_info']['backup_id']
            
            # Verify the backup
            verification_result = BackupService.verify_backup_integrity(backup_id)
            
            assert verification_result['success'] is True
            assert verification_result['backup_id'] == backup_id
            assert verification_result['integrity_check'] == 'passed'
    
    def test_backup_cleanup(self, app):
        """Test old backup cleanup"""
        with app.app_context():
            # Create some backups
            BackupService.create_database_backup("old_backup_1")
            BackupService.create_database_backup("old_backup_2")
            
            # Mock old backups by modifying retention period
            original_retention = BackupService.RETENTION_DAYS
            BackupService.RETENTION_DAYS = 0  # Clean up immediately
            
            try:
                cleanup_result = BackupService.cleanup_old_backups()
                
                assert cleanup_result['success'] is True
                assert cleanup_result['cleaned_count'] >= 0
                assert 'freed_mb' in cleanup_result
                
            finally:
                BackupService.RETENTION_DAYS = original_retention
    
    def test_backup_statistics(self, app):
        """Test backup statistics generation"""
        with app.app_context():
            # Create some backups
            BackupService.create_database_backup("stats_test_1")
            BackupService.create_database_backup("stats_test_2")
            
            stats = BackupService.get_backup_statistics()
            
            assert 'total_backups' in stats
            assert 'total_size_mb' in stats
            assert 'average_size_mb' in stats
            assert stats['total_backups'] >= 2
    
    def test_restore_database_backup(self, app):
        """Test database restoration from backup"""
        with app.app_context():
            # Create a backup
            result = BackupService.create_database_backup("restore_test")
            assert result['success'] is True
            
            backup_id = result['backup_info']['backup_id']
            
            # Create a temporary restore path
            restore_path = os.path.join(self.test_backup_dir, "restored_test.db")
            
            # Restore the backup
            restore_result = BackupService.restore_database_backup(backup_id, restore_path)
            
            assert restore_result['success'] is True
            assert restore_result['restored_path'] == restore_path
            assert 'backup_metadata' in restore_result
            assert 'tables_count' in restore_result
            
            # Check that restored file exists
            assert os.path.exists(restore_path)
            assert os.path.getsize(restore_path) > 0
    
    def test_backup_with_invalid_database(self, app):
        """Test backup creation with invalid database path"""
        with app.app_context():
            # Temporarily change database path to invalid location
            from config import Config
            original_db_uri = Config.SQLALCHEMY_DATABASE_URI
            Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///nonexistent/path/test.db'
            
            try:
                result = BackupService.create_database_backup("invalid_test")
                assert result['success'] is False
                assert 'error' in result
                
            finally:
                Config.SQLALCHEMY_DATABASE_URI = original_db_uri
    
    def test_verify_nonexistent_backup(self, app):
        """Test verification of nonexistent backup"""
        with app.app_context():
            result = BackupService.verify_backup_integrity("nonexistent_backup_id")
            
            assert result['success'] is False
            assert 'error' in result
            assert 'not found' in result['error'].lower()
    
    def test_restore_nonexistent_backup(self, app):
        """Test restoration of nonexistent backup"""
        with app.app_context():
            result = BackupService.restore_database_backup("nonexistent_backup_id")
            
            assert result['success'] is False
            assert 'error' in result
            assert 'not found' in result['error'].lower()
    
    def test_backup_encryption_key_generation(self, app):
        """Test encryption key generation and reuse"""
        with app.app_context():
            # Remove existing key file if it exists
            key_file = Path(BackupService.ENCRYPTION_KEY_FILE)
            if key_file.exists():
                key_file.unlink()
            
            # Get key (should generate new one)
            key1 = BackupService._get_encryption_key()
            assert len(key1) > 0
            assert key_file.exists()
            
            # Get key again (should reuse existing)
            key2 = BackupService._get_encryption_key()
            assert key1 == key2
    
    def test_backup_directory_creation(self, app):
        """Test backup directory creation"""
        with app.app_context():
            # Remove backup directory
            backup_path = Path(self.test_backup_dir)
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            # Ensure directory is created
            created_path = BackupService._ensure_backup_directory()
            
            assert created_path.exists()
            assert created_path.is_dir()
            assert str(created_path) == self.test_backup_dir