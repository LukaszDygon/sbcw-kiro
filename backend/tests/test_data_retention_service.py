"""
Tests for data retention service functionality
"""
import pytest
from datetime import datetime, timedelta
from services.data_retention_service import DataRetentionService
from models import (
    db, User, Account, Transaction, MoneyRequest, AuditLog, Notification,
    TransactionStatus, RequestStatus, UserRole
)
from decimal import Decimal

class TestDataRetentionService:
    """Test cases for DataRetentionService"""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, app):
        """Set up test data"""
        with app.app_context():
            # Create test user
            self.test_user = User(
                id='test-user-retention',
                microsoft_id='test-ms-retention',
                email='retention@example.com',
                name='Retention Test User',
                role=UserRole.EMPLOYEE
            )
            db.session.add(self.test_user)
            
            # Create test account
            self.test_account = Account(
                id='test-account-retention',
                user_id=self.test_user.id,
                balance=Decimal('100.00')
            )
            db.session.add(self.test_account)
            
            # Create old failed transaction
            old_date = datetime.utcnow() - timedelta(days=400)
            self.old_failed_transaction = Transaction(
                id='old-failed-transaction',
                sender_id=self.test_user.id,
                recipient_id=self.test_user.id,
                amount=Decimal('50.00'),
                status=TransactionStatus.FAILED,
                created_at=old_date
            )
            db.session.add(self.old_failed_transaction)
            
            # Create recent failed transaction
            self.recent_failed_transaction = Transaction(
                id='recent-failed-transaction',
                sender_id=self.test_user.id,
                recipient_id=self.test_user.id,
                amount=Decimal('25.00'),
                status=TransactionStatus.FAILED,
                created_at=datetime.utcnow() - timedelta(days=30)
            )
            db.session.add(self.recent_failed_transaction)
            
            # Create old expired money request
            self.old_expired_request = MoneyRequest(
                id='old-expired-request',
                requester_id=self.test_user.id,
                recipient_id=self.test_user.id,
                amount=Decimal('75.00'),
                status=RequestStatus.EXPIRED,
                created_at=old_date
            )
            db.session.add(self.old_expired_request)
            
            # Create recent expired money request
            self.recent_expired_request = MoneyRequest(
                id='recent-expired-request',
                requester_id=self.test_user.id,
                recipient_id=self.test_user.id,
                amount=Decimal('30.00'),
                status=RequestStatus.EXPIRED,
                created_at=datetime.utcnow() - timedelta(days=30)
            )
            db.session.add(self.recent_expired_request)
            
            # Create old notification
            self.old_notification = Notification(
                id='old-notification',
                user_id=self.test_user.id,
                title='Old Notification',
                message='This is an old notification',
                created_at=old_date
            )
            db.session.add(self.old_notification)
            
            # Create recent notification
            self.recent_notification = Notification(
                id='recent-notification',
                user_id=self.test_user.id,
                title='Recent Notification',
                message='This is a recent notification',
                created_at=datetime.utcnow() - timedelta(days=30)
            )
            db.session.add(self.recent_notification)
            
            # Create old audit log
            self.old_audit_log = AuditLog(
                id='old-audit-log',
                user_id=self.test_user.id,
                action_type='TEST_ACTION',
                entity_type='TEST_ENTITY',
                entity_id='test-entity-id',
                created_at=datetime.utcnow() - timedelta(days=3000)  # Very old
            )
            db.session.add(self.old_audit_log)
            
            db.session.commit()
            
            yield
            
            # Cleanup is handled by test database rollback
    
    def test_get_retention_policies(self, app):
        """Test getting retention policies"""
        with app.app_context():
            policies = DataRetentionService.get_retention_policies()
            
            assert isinstance(policies, dict)
            assert 'audit_logs' in policies
            assert 'completed_transactions' in policies
            assert 'failed_transactions' in policies
            assert 'expired_money_requests' in policies
            assert 'user_notifications' in policies
            
            # Check that all values are positive integers
            for policy_name, days in policies.items():
                assert isinstance(days, int)
                assert days > 0
    
    def test_update_retention_policy(self, app):
        """Test updating retention policy"""
        with app.app_context():
            original_policies = DataRetentionService.get_retention_policies()
            original_value = original_policies['failed_transactions']
            
            # Update policy
            new_value = original_value + 10
            result = DataRetentionService.update_retention_policy('failed_transactions', new_value)
            
            assert result['success'] is True
            assert result['policy_name'] == 'failed_transactions'
            assert result['old_retention_days'] == original_value
            assert result['new_retention_days'] == new_value
            
            # Verify policy was updated
            updated_policies = DataRetentionService.get_retention_policies()
            assert updated_policies['failed_transactions'] == new_value
    
    def test_update_invalid_retention_policy(self, app):
        """Test updating invalid retention policy"""
        with app.app_context():
            # Test invalid policy name
            result = DataRetentionService.update_retention_policy('invalid_policy', 30)
            assert result['success'] is False
            assert 'Unknown retention policy' in result['error']
            
            # Test invalid retention days
            result = DataRetentionService.update_retention_policy('failed_transactions', 0)
            assert result['success'] is False
            assert 'at least 1 day' in result['error']
    
    def test_cleanup_expired_money_requests(self, app):
        """Test cleanup of expired money requests"""
        with app.app_context():
            # Set short retention period for testing
            original_retention = DataRetentionService.RETENTION_POLICIES['expired_money_requests']
            DataRetentionService.RETENTION_POLICIES['expired_money_requests'] = 100  # 100 days
            
            try:
                result = DataRetentionService.cleanup_expired_money_requests()
                
                assert result['success'] is True
                assert result['cleaned_count'] >= 1  # Should clean up old expired request
                assert 'retention_days' in result
                assert 'cutoff_date' in result
                
                # Verify old request was deleted
                old_request = MoneyRequest.query.get(self.old_expired_request.id)
                assert old_request is None
                
                # Verify recent request still exists
                recent_request = MoneyRequest.query.get(self.recent_expired_request.id)
                assert recent_request is not None
                
            finally:
                DataRetentionService.RETENTION_POLICIES['expired_money_requests'] = original_retention
    
    def test_cleanup_old_notifications(self, app):
        """Test cleanup of old notifications"""
        with app.app_context():
            # Set short retention period for testing
            original_retention = DataRetentionService.RETENTION_POLICIES['user_notifications']
            DataRetentionService.RETENTION_POLICIES['user_notifications'] = 200  # 200 days
            
            try:
                result = DataRetentionService.cleanup_old_notifications()
                
                assert result['success'] is True
                assert result['cleaned_count'] >= 1  # Should clean up old notification
                
                # Verify old notification was deleted
                old_notification = Notification.query.get(self.old_notification.id)
                assert old_notification is None
                
                # Verify recent notification still exists
                recent_notification = Notification.query.get(self.recent_notification.id)
                assert recent_notification is not None
                
            finally:
                DataRetentionService.RETENTION_POLICIES['user_notifications'] = original_retention
    
    def test_cleanup_failed_transactions(self, app):
        """Test cleanup of failed transactions"""
        with app.app_context():
            # Set short retention period for testing
            original_retention = DataRetentionService.RETENTION_POLICIES['failed_transactions']
            DataRetentionService.RETENTION_POLICIES['failed_transactions'] = 200  # 200 days
            
            try:
                result = DataRetentionService.cleanup_failed_transactions()
                
                assert result['success'] is True
                assert result['cleaned_count'] >= 1  # Should clean up old failed transaction
                
                # Verify old failed transaction was deleted
                old_transaction = Transaction.query.get(self.old_failed_transaction.id)
                assert old_transaction is None
                
                # Verify recent failed transaction still exists
                recent_transaction = Transaction.query.get(self.recent_failed_transaction.id)
                assert recent_transaction is not None
                
            finally:
                DataRetentionService.RETENTION_POLICIES['failed_transactions'] = original_retention
    
    def test_archive_old_audit_logs(self, app):
        """Test archival of old audit logs"""
        with app.app_context():
            result = DataRetentionService.archive_old_audit_logs()
            
            assert result['success'] is True
            assert 'logs_to_archive' in result
            assert result['logs_to_archive'] >= 0
            assert 'note' in result
            assert 'compliance' in result['note']
            
            # Verify audit log still exists (not deleted for compliance)
            old_log = AuditLog.query.get(self.old_audit_log.id)
            assert old_log is not None
    
    def test_get_data_retention_status(self, app):
        """Test getting data retention status"""
        with app.app_context():
            result = DataRetentionService.get_data_retention_status()
            
            assert result['success'] is True
            assert 'status' in result
            
            status = result['status']
            assert 'retention_policies' in status
            assert 'data_counts' in status
            assert 'cleanup_candidates' in status
            
            # Check data counts
            data_counts = status['data_counts']
            assert 'total_transactions' in data_counts
            assert 'failed_transactions' in data_counts
            assert 'total_money_requests' in data_counts
            assert 'total_notifications' in data_counts
            assert 'total_audit_logs' in data_counts
            
            # Check cleanup candidates
            cleanup_candidates = status['cleanup_candidates']
            for policy_name in DataRetentionService.RETENTION_POLICIES.keys():
                if policy_name in cleanup_candidates:
                    candidate_info = cleanup_candidates[policy_name]
                    assert 'count' in candidate_info
                    assert 'retention_days' in candidate_info
                    assert 'cutoff_date' in candidate_info
    
    def test_run_full_cleanup(self, app):
        """Test running full data cleanup"""
        with app.app_context():
            # Set short retention periods for testing
            original_policies = DataRetentionService.RETENTION_POLICIES.copy()
            DataRetentionService.RETENTION_POLICIES.update({
                'expired_money_requests': 100,
                'failed_transactions': 200,
                'user_notifications': 200
            })
            
            try:
                result = DataRetentionService.run_full_cleanup()
                
                assert result['success'] is True
                assert 'cleanup_results' in result
                assert 'total_cleaned' in result
                assert 'errors' in result
                
                cleanup_results = result['cleanup_results']
                assert 'expired_money_requests' in cleanup_results
                assert 'old_notifications' in cleanup_results
                assert 'failed_transactions' in cleanup_results
                assert 'audit_logs_archive' in cleanup_results
                
                # Check that some cleanup occurred
                assert result['total_cleaned'] >= 0
                
            finally:
                DataRetentionService.RETENTION_POLICIES.update(original_policies)
    
    def test_validate_retention_compliance(self, app):
        """Test retention compliance validation"""
        with app.app_context():
            result = DataRetentionService.validate_retention_compliance()
            
            assert result['success'] is True
            assert 'compliance' in result
            
            compliance = result['compliance']
            assert 'compliant' in compliance
            assert 'violations' in compliance
            assert 'warnings' in compliance
            assert 'recommendations' in compliance
            
            assert isinstance(compliance['compliant'], bool)
            assert isinstance(compliance['violations'], list)
            assert isinstance(compliance['warnings'], list)
            assert isinstance(compliance['recommendations'], list)
    
    def test_compliance_with_violations(self, app):
        """Test compliance validation with violations"""
        with app.app_context():
            # Create many old items to trigger violations
            old_date = datetime.utcnow() - timedelta(days=400)
            
            # Create many old failed transactions
            for i in range(150):  # Above violation threshold
                transaction = Transaction(
                    id=f'violation-transaction-{i}',
                    sender_id=self.test_user.id,
                    recipient_id=self.test_user.id,
                    amount=Decimal('1.00'),
                    status=TransactionStatus.FAILED,
                    created_at=old_date
                )
                db.session.add(transaction)
            
            db.session.commit()
            
            # Set short retention period
            original_retention = DataRetentionService.RETENTION_POLICIES['failed_transactions']
            DataRetentionService.RETENTION_POLICIES['failed_transactions'] = 200
            
            try:
                result = DataRetentionService.validate_retention_compliance()
                
                assert result['success'] is True
                compliance = result['compliance']
                
                # Should have violations due to many old failed transactions
                assert compliance['compliant'] is False
                assert len(compliance['violations']) > 0
                
                # Check violation details
                violation = compliance['violations'][0]
                assert 'policy' in violation
                assert 'issue' in violation
                assert 'recommendation' in violation
                
            finally:
                DataRetentionService.RETENTION_POLICIES['failed_transactions'] = original_retention