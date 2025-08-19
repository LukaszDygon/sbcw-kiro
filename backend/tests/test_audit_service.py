"""
Tests for AuditService
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from services.audit_service import AuditService
from models import (
    db, User, UserRole, AccountStatus, Account, 
    Transaction, TransactionType, AuditLog, AuditAction
)

class TestAuditService:
    """Test cases for AuditService"""
    
    def test_log_transaction_success(self, app):
        """Test logging transaction audit"""
        with app.app_context():
            # Create users and accounts
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.flush()
            
            # Create transaction
            transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                note='Test payment'
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Test audit logging
            audit_log = AuditService.log_transaction(
                transaction=transaction,
                ip_address='192.168.1.1',
                user_agent='Test Browser'
            )
            
            assert audit_log.user_id == sender.id
            assert audit_log.action == AuditAction.TRANSACTION_CREATED
            assert audit_log.entity_type == 'Transaction'
            assert audit_log.entity_id == transaction.id
            assert audit_log.ip_address == '192.168.1.1'
            assert audit_log.user_agent == 'Test Browser'
            assert audit_log.details['amount'] == '25.00'
            assert audit_log.details['recipient_id'] == recipient.id
    
    def test_log_user_action(self, app):
        """Test logging user action audit"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Test audit logging
            audit_log = AuditService.log_user_action(
                user_id=user.id,
                action=AuditAction.USER_LOGIN,
                details={'login_method': 'microsoft_sso'},
                ip_address='192.168.1.1',
                user_agent='Test Browser'
            )
            
            assert audit_log.user_id == user.id
            assert audit_log.action == AuditAction.USER_LOGIN
            assert audit_log.entity_type == 'User'
            assert audit_log.entity_id == user.id
            assert audit_log.details['login_method'] == 'microsoft_sso'
            assert audit_log.ip_address == '192.168.1.1'
    
    def test_log_system_event(self, app):
        """Test logging system event audit"""
        with app.app_context():
            # Test system event logging
            audit_log = AuditService.log_system_event(
                action=AuditAction.SYSTEM_MAINTENANCE,
                details={'maintenance_type': 'database_backup'},
                ip_address='127.0.0.1'
            )
            
            assert audit_log.user_id is None  # System events have no user
            assert audit_log.action == AuditAction.SYSTEM_MAINTENANCE
            assert audit_log.entity_type == 'System'
            assert audit_log.details['maintenance_type'] == 'database_backup'
            assert audit_log.ip_address == '127.0.0.1'
    
    def test_log_data_modification(self, app):
        """Test logging data modification audit"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Test data modification logging
            old_values = {'name': 'Old Name', 'email': 'old@test.com'}
            new_values = {'name': 'New Name', 'email': 'new@test.com'}
            
            audit_log = AuditService.log_data_modification(
                user_id=user.id,
                entity_type='User',
                entity_id=user.id,
                old_values=old_values,
                new_values=new_values,
                ip_address='192.168.1.1',
                user_agent='Test Browser'
            )
            
            assert audit_log.user_id == user.id
            assert audit_log.action == AuditAction.DATA_MODIFIED
            assert audit_log.entity_type == 'User'
            assert audit_log.entity_id == user.id
            assert audit_log.old_values == old_values
            assert audit_log.new_values == new_values
    
    def test_get_user_audit_trail(self, app):
        """Test getting user audit trail"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create audit logs
            login_log = AuditLog(
                user_id=user.id,
                action=AuditAction.USER_LOGIN,
                entity_type='User',
                entity_id=user.id,
                details={'login_method': 'microsoft_sso'},
                ip_address='192.168.1.1'
            )
            logout_log = AuditLog(
                user_id=user.id,
                action=AuditAction.USER_LOGOUT,
                entity_type='User',
                entity_id=user.id,
                details={},
                ip_address='192.168.1.1'
            )
            db.session.add_all([login_log, logout_log])
            db.session.commit()
            
            # Test getting audit trail
            audit_trail = AuditService.get_user_audit_trail(user.id, days=30)
            
            assert len(audit_trail) == 2
            assert any(log['action'] == AuditAction.USER_LOGIN.value for log in audit_trail)
            assert any(log['action'] == AuditAction.USER_LOGOUT.value for log in audit_trail)
    
    def test_get_transaction_audit_trail(self, app):
        """Test getting transaction audit trail"""
        with app.app_context():
            # Create users and transaction
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Create audit logs for transaction
            created_log = AuditLog(
                user_id=sender.id,
                action=AuditAction.TRANSACTION_CREATED,
                entity_type='Transaction',
                entity_id=transaction.id,
                details={'amount': '25.00'},
                ip_address='192.168.1.1'
            )
            processed_log = AuditLog(
                user_id=sender.id,
                action=AuditAction.TRANSACTION_PROCESSED,
                entity_type='Transaction',
                entity_id=transaction.id,
                details={'status': 'completed'},
                ip_address='192.168.1.1'
            )
            db.session.add_all([created_log, processed_log])
            db.session.commit()
            
            # Test getting transaction audit trail
            audit_trail = AuditService.get_transaction_audit_trail(transaction.id)
            
            assert len(audit_trail) == 2
            assert any(log['action'] == AuditAction.TRANSACTION_CREATED.value for log in audit_trail)
            assert any(log['action'] == AuditAction.TRANSACTION_PROCESSED.value for log in audit_trail)
    
    def test_get_system_audit_trail(self, app):
        """Test getting system audit trail"""
        with app.app_context():
            # Create system audit logs
            maintenance_log = AuditLog(
                user_id=None,
                action=AuditAction.SYSTEM_MAINTENANCE,
                entity_type='System',
                entity_id='system',
                details={'maintenance_type': 'backup'},
                ip_address='127.0.0.1'
            )
            startup_log = AuditLog(
                user_id=None,
                action=AuditAction.SYSTEM_STARTUP,
                entity_type='System',
                entity_id='system',
                details={'version': '1.0.0'},
                ip_address='127.0.0.1'
            )
            db.session.add_all([maintenance_log, startup_log])
            db.session.commit()
            
            # Test getting system audit trail
            audit_trail = AuditService.get_system_audit_trail(days=30)
            
            assert len(audit_trail) == 2
            assert any(log['action'] == AuditAction.SYSTEM_MAINTENANCE.value for log in audit_trail)
            assert any(log['action'] == AuditAction.SYSTEM_STARTUP.value for log in audit_trail)
    
    def test_generate_audit_report(self, app):
        """Test generating audit report"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create various audit logs
            login_log = AuditLog(
                user_id=user.id,
                action=AuditAction.USER_LOGIN,
                entity_type='User',
                entity_id=user.id,
                details={'login_method': 'microsoft_sso'},
                ip_address='192.168.1.1'
            )
            transaction_log = AuditLog(
                user_id=user.id,
                action=AuditAction.TRANSACTION_CREATED,
                entity_type='Transaction',
                entity_id='trans-123',
                details={'amount': '25.00'},
                ip_address='192.168.1.1'
            )
            system_log = AuditLog(
                user_id=None,
                action=AuditAction.SYSTEM_MAINTENANCE,
                entity_type='System',
                entity_id='system',
                details={'maintenance_type': 'backup'},
                ip_address='127.0.0.1'
            )
            db.session.add_all([login_log, transaction_log, system_log])
            db.session.commit()
            
            # Test generating report
            start_date = datetime.utcnow() - timedelta(days=1)
            end_date = datetime.utcnow() + timedelta(days=1)
            
            report = AuditService.generate_audit_report(
                start_date=start_date,
                end_date=end_date
            )
            
            assert report['total_events'] == 3
            assert report['user_actions'] == 2  # login and transaction
            assert report['system_events'] == 1  # maintenance
            assert len(report['events']) == 3
            assert report['date_range']['start'] == start_date.isoformat()
            assert report['date_range']['end'] == end_date.isoformat()
    
    def test_search_audit_logs(self, app):
        """Test searching audit logs"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create audit logs
            login_log = AuditLog(
                user_id=user.id,
                action=AuditAction.USER_LOGIN,
                entity_type='User',
                entity_id=user.id,
                details={'login_method': 'microsoft_sso'},
                ip_address='192.168.1.1'
            )
            transaction_log = AuditLog(
                user_id=user.id,
                action=AuditAction.TRANSACTION_CREATED,
                entity_type='Transaction',
                entity_id='trans-123',
                details={'amount': '25.00', 'recipient': 'test@example.com'},
                ip_address='192.168.1.2'
            )
            db.session.add_all([login_log, transaction_log])
            db.session.commit()
            
            # Test searching by action
            login_results = AuditService.search_audit_logs(
                action=AuditAction.USER_LOGIN,
                days=30
            )
            assert len(login_results) == 1
            assert login_results[0]['action'] == AuditAction.USER_LOGIN.value
            
            # Test searching by IP address
            ip_results = AuditService.search_audit_logs(
                ip_address='192.168.1.2',
                days=30
            )
            assert len(ip_results) == 1
            assert ip_results[0]['ip_address'] == '192.168.1.2'
            
            # Test searching by user
            user_results = AuditService.search_audit_logs(
                user_id=user.id,
                days=30
            )
            assert len(user_results) == 2
    
    def test_get_audit_statistics(self, app):
        """Test getting audit statistics"""
        with app.app_context():
            # Create users
            user1 = User(microsoft_id='user1', email='user1@test.com', name='User 1')
            user2 = User(microsoft_id='user2', email='user2@test.com', name='User 2')
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # Create audit logs
            logs = [
                AuditLog(
                    user_id=user1.id,
                    action=AuditAction.USER_LOGIN,
                    entity_type='User',
                    entity_id=user1.id,
                    ip_address='192.168.1.1'
                ),
                AuditLog(
                    user_id=user1.id,
                    action=AuditAction.TRANSACTION_CREATED,
                    entity_type='Transaction',
                    entity_id='trans-1',
                    ip_address='192.168.1.1'
                ),
                AuditLog(
                    user_id=user2.id,
                    action=AuditAction.USER_LOGIN,
                    entity_type='User',
                    entity_id=user2.id,
                    ip_address='192.168.1.2'
                ),
                AuditLog(
                    user_id=None,
                    action=AuditAction.SYSTEM_MAINTENANCE,
                    entity_type='System',
                    entity_id='system',
                    ip_address='127.0.0.1'
                )
            ]
            db.session.add_all(logs)
            db.session.commit()
            
            # Test getting statistics
            stats = AuditService.get_audit_statistics(days=30)
            
            assert stats['total_events'] == 4
            assert stats['unique_users'] == 2
            assert stats['user_actions'] == 3
            assert stats['system_events'] == 1
            assert AuditAction.USER_LOGIN.value in stats['action_breakdown']
            assert stats['action_breakdown'][AuditAction.USER_LOGIN.value] == 2
    
    def test_verify_audit_integrity(self, app):
        """Test verifying audit log integrity"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create audit log
            audit_log = AuditLog(
                user_id=user.id,
                action=AuditAction.USER_LOGIN,
                entity_type='User',
                entity_id=user.id,
                details={'login_method': 'microsoft_sso'},
                ip_address='192.168.1.1'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            # Test integrity verification
            integrity_result = AuditService.verify_audit_integrity(audit_log.id)
            
            assert integrity_result['valid'] is True
            assert 'checksum' in integrity_result
            assert integrity_result['verified_at'] is not None
    
    def test_export_audit_logs(self, app):
        """Test exporting audit logs"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create audit logs
            logs = [
                AuditLog(
                    user_id=user.id,
                    action=AuditAction.USER_LOGIN,
                    entity_type='User',
                    entity_id=user.id,
                    details={'login_method': 'microsoft_sso'},
                    ip_address='192.168.1.1'
                ),
                AuditLog(
                    user_id=user.id,
                    action=AuditAction.TRANSACTION_CREATED,
                    entity_type='Transaction',
                    entity_id='trans-123',
                    details={'amount': '25.00'},
                    ip_address='192.168.1.1'
                )
            ]
            db.session.add_all(logs)
            db.session.commit()
            
            # Test CSV export
            start_date = datetime.utcnow() - timedelta(days=1)
            end_date = datetime.utcnow() + timedelta(days=1)
            
            csv_export = AuditService.export_audit_logs(
                start_date=start_date,
                end_date=end_date,
                format='csv'
            )
            
            assert csv_export['success'] is True
            assert csv_export['format'] == 'csv'
            assert 'data' in csv_export
            assert len(csv_export['data'].split('\n')) >= 3  # Header + 2 data rows
            
            # Test JSON export
            json_export = AuditService.export_audit_logs(
                start_date=start_date,
                end_date=end_date,
                format='json'
            )
            
            assert json_export['success'] is True
            assert json_export['format'] == 'json'
            assert isinstance(json_export['data'], list)
            assert len(json_export['data']) == 2
    
    def test_cleanup_old_audit_logs(self, app):
        """Test cleaning up old audit logs"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create old audit log
            old_log = AuditLog(
                user_id=user.id,
                action=AuditAction.USER_LOGIN,
                entity_type='User',
                entity_id=user.id,
                details={'login_method': 'microsoft_sso'},
                ip_address='192.168.1.1'
            )
            # Manually set old created_at date
            old_log.created_at = datetime.utcnow() - timedelta(days=400)
            
            # Create recent audit log
            recent_log = AuditLog(
                user_id=user.id,
                action=AuditAction.USER_LOGOUT,
                entity_type='User',
                entity_id=user.id,
                details={},
                ip_address='192.168.1.1'
            )
            
            db.session.add_all([old_log, recent_log])
            db.session.commit()
            
            # Test cleanup (keep logs for 365 days)
            result = AuditService.cleanup_old_audit_logs(retention_days=365)
            
            assert result['success'] is True
            assert result['deleted_count'] == 1
            
            # Verify old log was deleted
            remaining_logs = AuditLog.query.filter_by(user_id=user.id).all()
            assert len(remaining_logs) == 1
            assert remaining_logs[0].action == AuditAction.USER_LOGOUT