"""
Tests for backup API endpoints
"""
import pytest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from models import User, UserRole
from services.backup_service import BackupService

class TestBackupAPI:
    """Test cases for backup API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, app, client):
        """Set up test environment"""
        with app.app_context():
            # Create test backup directory
            self.test_backup_dir = tempfile.mkdtemp()
            BackupService.BACKUP_DIR = self.test_backup_dir
            
            # Create admin user for testing
            self.admin_user = User(
                id='admin-user-backup',
                microsoft_id='admin-ms-backup',
                email='admin@example.com',
                name='Admin User',
                role=UserRole.ADMIN
            )
            
            # Create regular user for testing
            self.regular_user = User(
                id='regular-user-backup',
                microsoft_id='regular-ms-backup',
                email='user@example.com',
                name='Regular User',
                role=UserRole.EMPLOYEE
            )
            
            yield
            
            # Cleanup
            shutil.rmtree(self.test_backup_dir, ignore_errors=True)
    
    def test_create_backup_success(self, client, app):
        """Test successful backup creation"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.backup_service.BackupService.create_database_backup') as mock_backup:
                    mock_backup.return_value = {
                        'success': True,
                        'backup_info': {
                            'backup_id': '20241201_120000',
                            'filename': 'test_backup_20241201_120000.db.gz.enc',
                            'size_mb': 5.2,
                            'created_at': '2024-12-01T12:00:00'
                        }
                    }
                    
                    response = client.post('/api/backup/create', 
                                         json={'backup_name': 'test_backup'},
                                         headers={'Content-Type': 'application/json'})
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'backup_info' in data
                    assert data['backup_info']['backup_id'] == '20241201_120000'
    
    def test_create_backup_unauthorized(self, client, app):
        """Test backup creation without authentication"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=None):
                response = client.post('/api/backup/create', 
                                     json={'backup_name': 'test_backup'},
                                     headers={'Content-Type': 'application/json'})
                
                assert response.status_code == 401
                data = json.loads(response.data)
                assert 'error' in data
    
    def test_create_backup_forbidden(self, client, app):
        """Test backup creation with regular user (forbidden)"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.regular_user):
                response = client.post('/api/backup/create', 
                                     json={'backup_name': 'test_backup'},
                                     headers={'Content-Type': 'application/json'})
                
                assert response.status_code == 403
                data = json.loads(response.data)
                assert 'error' in data
                assert 'Admin access required' in data['error']
    
    def test_list_backups_success(self, client, app):
        """Test successful backup listing"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.backup_service.BackupService.list_backups') as mock_list:
                    mock_list.return_value = [
                        {
                            'backup_id': '20241201_120000',
                            'filename': 'backup_20241201_120000.db.gz.enc',
                            'created_at': '2024-12-01T12:00:00',
                            'size_mb': 5.2,
                            'file_exists': True
                        },
                        {
                            'backup_id': '20241130_120000',
                            'filename': 'backup_20241130_120000.db.gz.enc',
                            'created_at': '2024-11-30T12:00:00',
                            'size_mb': 4.8,
                            'file_exists': True
                        }
                    ]
                    
                    response = client.get('/api/backup/list')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'backups' in data
                    assert len(data['backups']) == 2
                    assert data['total_count'] == 2
    
    def test_restore_backup_success(self, client, app):
        """Test successful backup restoration"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.backup_service.BackupService.restore_database_backup') as mock_restore:
                    mock_restore.return_value = {
                        'success': True,
                        'restored_path': '/tmp/restored_test.db',
                        'backup_metadata': {
                            'backup_id': '20241201_120000',
                            'created_at': '2024-12-01T12:00:00'
                        },
                        'tables_count': 8
                    }
                    
                    response = client.post('/api/backup/restore',
                                         json={
                                             'backup_id': '20241201_120000',
                                             'target_path': '/tmp/restored_test.db'
                                         },
                                         headers={'Content-Type': 'application/json'})
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'restoration_info' in data
                    assert data['restoration_info']['tables_count'] == 8
    
    def test_restore_backup_missing_id(self, client, app):
        """Test backup restoration without backup ID"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                response = client.post('/api/backup/restore',
                                     json={},
                                     headers={'Content-Type': 'application/json'})
                
                assert response.status_code == 400
                data = json.loads(response.data)
                assert data['success'] is False
                assert 'backup_id is required' in data['error']
    
    def test_verify_backup_success(self, client, app):
        """Test successful backup verification"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.backup_service.BackupService.verify_backup_integrity') as mock_verify:
                    mock_verify.return_value = {
                        'success': True,
                        'backup_id': '20241201_120000',
                        'file_size_mb': 5.2,
                        'integrity_check': 'passed'
                    }
                    
                    response = client.get('/api/backup/verify/20241201_120000')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'verification_info' in data
                    assert data['verification_info']['integrity_check'] == 'passed'
    
    def test_cleanup_backups_success(self, client, app):
        """Test successful backup cleanup"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.backup_service.BackupService.cleanup_old_backups') as mock_cleanup:
                    mock_cleanup.return_value = {
                        'success': True,
                        'cleaned_count': 3,
                        'freed_mb': 15.6,
                        'retention_days': 30
                    }
                    
                    response = client.post('/api/backup/cleanup')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'cleanup_info' in data
                    assert data['cleanup_info']['cleaned_count'] == 3
    
    def test_get_backup_statistics(self, client, app):
        """Test getting backup statistics"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.backup_service.BackupService.get_backup_statistics') as mock_stats:
                    mock_stats.return_value = {
                        'total_backups': 5,
                        'total_size_mb': 25.8,
                        'average_size_mb': 5.16,
                        'oldest_backup': {
                            'id': '20241101_120000',
                            'created_at': '2024-11-01T12:00:00',
                            'size_mb': 4.2
                        },
                        'newest_backup': {
                            'id': '20241201_120000',
                            'created_at': '2024-12-01T12:00:00',
                            'size_mb': 5.2
                        }
                    }
                    
                    response = client.get('/api/backup/statistics')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'statistics' in data
                    assert data['statistics']['total_backups'] == 5
    
    def test_get_retention_policies(self, client, app):
        """Test getting retention policies"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.data_retention_service.DataRetentionService.get_retention_policies') as mock_policies:
                    mock_policies.return_value = {
                        'audit_logs': 2555,
                        'completed_transactions': 2555,
                        'failed_transactions': 365,
                        'expired_money_requests': 90,
                        'user_notifications': 180
                    }
                    
                    response = client.get('/api/backup/retention/policies')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'policies' in data
                    assert data['policies']['audit_logs'] == 2555
    
    def test_update_retention_policy_success(self, client, app):
        """Test successful retention policy update"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.data_retention_service.DataRetentionService.update_retention_policy') as mock_update:
                    mock_update.return_value = {
                        'success': True,
                        'policy_name': 'failed_transactions',
                        'old_retention_days': 365,
                        'new_retention_days': 400
                    }
                    
                    response = client.put('/api/backup/retention/policies',
                                        json={
                                            'policy_name': 'failed_transactions',
                                            'retention_days': 400
                                        },
                                        headers={'Content-Type': 'application/json'})
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'update_info' in data
                    assert data['update_info']['new_retention_days'] == 400
    
    def test_update_retention_policy_missing_params(self, client, app):
        """Test retention policy update with missing parameters"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                response = client.put('/api/backup/retention/policies',
                                    json={'policy_name': 'failed_transactions'},
                                    headers={'Content-Type': 'application/json'})
                
                assert response.status_code == 400
                data = json.loads(response.data)
                assert data['success'] is False
                assert 'retention_days are required' in data['error']
    
    def test_get_retention_status(self, client, app):
        """Test getting retention status"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.data_retention_service.DataRetentionService.get_data_retention_status') as mock_status:
                    mock_status.return_value = {
                        'success': True,
                        'status': {
                            'retention_policies': {
                                'failed_transactions': 365
                            },
                            'data_counts': {
                                'total_transactions': 1000,
                                'failed_transactions': 50
                            },
                            'cleanup_candidates': {
                                'failed_transactions': {
                                    'count': 10,
                                    'retention_days': 365
                                }
                            }
                        }
                    }
                    
                    response = client.get('/api/backup/retention/status')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'retention_status' in data
                    assert 'data_counts' in data['retention_status']
    
    def test_run_data_cleanup(self, client, app):
        """Test running data cleanup"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.data_retention_service.DataRetentionService.run_full_cleanup') as mock_cleanup:
                    mock_cleanup.return_value = {
                        'success': True,
                        'cleanup_results': {
                            'expired_money_requests': {'success': True, 'cleaned_count': 5},
                            'old_notifications': {'success': True, 'cleaned_count': 10}
                        },
                        'total_cleaned': 15,
                        'errors': []
                    }
                    
                    response = client.post('/api/backup/retention/cleanup')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'cleanup_results' in data
                    assert data['cleanup_results']['total_cleaned'] == 15
    
    def test_validate_compliance(self, client, app):
        """Test compliance validation"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.data_retention_service.DataRetentionService.validate_retention_compliance') as mock_validate:
                    mock_validate.return_value = {
                        'success': True,
                        'compliance': {
                            'compliant': True,
                            'violations': [],
                            'warnings': [],
                            'recommendations': []
                        }
                    }
                    
                    response = client.get('/api/backup/retention/compliance')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'compliance' in data
                    assert data['compliance']['compliant'] is True
    
    def test_scheduler_status(self, client, app):
        """Test getting scheduler status"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.scheduler_service.scheduler_service.get_scheduler_status') as mock_status:
                    mock_status.return_value = {
                        'success': True,
                        'is_running': True,
                        'jobs': [
                            {
                                'id': 'daily_backup',
                                'name': 'Daily Database Backup',
                                'next_run': '2024-12-02T02:00:00',
                                'trigger': 'cron[hour=2,minute=0]'
                            }
                        ],
                        'job_count': 1
                    }
                    
                    response = client.get('/api/backup/scheduler/status')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'scheduler_status' in data
                    assert data['scheduler_status']['is_running'] is True
    
    def test_start_scheduler(self, client, app):
        """Test starting scheduler"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.scheduler_service.scheduler_service.start_scheduler') as mock_start:
                    mock_start.return_value = {
                        'success': True,
                        'message': 'Scheduler started successfully',
                        'jobs_scheduled': 4
                    }
                    
                    response = client.post('/api/backup/scheduler/start')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'scheduler_info' in data
    
    def test_stop_scheduler(self, client, app):
        """Test stopping scheduler"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.scheduler_service.scheduler_service.stop_scheduler') as mock_stop:
                    mock_stop.return_value = {
                        'success': True,
                        'message': 'Scheduler stopped successfully'
                    }
                    
                    response = client.post('/api/backup/scheduler/stop')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
    
    def test_run_scheduled_job(self, client, app):
        """Test running scheduled job manually"""
        with app.app_context():
            with patch('services.auth_service.AuthService.get_current_user', return_value=self.admin_user):
                with patch('services.scheduler_service.scheduler_service.run_job_manually') as mock_run:
                    mock_run.return_value = {
                        'success': True,
                        'message': 'Job daily_backup executed manually'
                    }
                    
                    response = client.post('/api/backup/scheduler/run/daily_backup')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'execution_info' in data
    
    def test_health_check(self, client, app):
        """Test backup service health check"""
        with app.app_context():
            response = client.get('/api/backup/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['service'] == 'backup'
            assert data['status'] == 'healthy'