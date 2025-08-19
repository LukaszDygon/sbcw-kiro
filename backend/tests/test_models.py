"""
Tests for SoftBankCashWire database models
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from models import (
    db, User, UserRole, AccountStatus, Account, 
    Transaction, TransactionType, TransactionStatus,
    EventAccount, EventStatus, MoneyRequest, RequestStatus,
    AuditLog, AuditAction, Notification, NotificationType, NotificationStatus
)

class TestUserModel:
    """Test cases for User model"""
    
    def test_create_user(self, app):
        """Test creating a new user"""
        with app.app_context():
            user = User(
                microsoft_id="test-123",
                email="test@softbank.com",
                name="Test User",
                role=UserRole.EMPLOYEE
            )
            
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.microsoft_id == "test-123"
            assert user.email == "test@softbank.com"
            assert user.name == "Test User"
            assert user.role == UserRole.EMPLOYEE
            assert user.account_status == AccountStatus.ACTIVE
            assert user.is_active()
    
    def test_user_roles(self, app):
        """Test user role methods"""
        with app.app_context():
            employee = User(microsoft_id="emp", email="emp@test.com", name="Employee")
            admin = User(microsoft_id="admin", email="admin@test.com", name="Admin", role=UserRole.ADMIN)
            finance = User(microsoft_id="fin", email="fin@test.com", name="Finance", role=UserRole.FINANCE)
            
            db.session.add_all([employee, admin, finance])
            db.session.commit()
            
            assert employee.has_role(UserRole.EMPLOYEE)
            assert not employee.can_access_admin_features()
            assert not employee.can_access_finance_features()
            
            assert admin.has_role(UserRole.ADMIN)
            assert admin.can_access_admin_features()
            assert not admin.can_access_finance_features()
            
            assert finance.has_role(UserRole.FINANCE)
            assert finance.can_access_admin_features()
            assert finance.can_access_finance_features()
    
    def test_user_account_status(self, app):
        """Test user account status methods"""
        with app.app_context():
            active_user = User(microsoft_id="active", email="active@test.com", name="Active")
            suspended_user = User(
                microsoft_id="suspended", 
                email="suspended@test.com", 
                name="Suspended",
                account_status=AccountStatus.SUSPENDED
            )
            closed_user = User(
                microsoft_id="closed", 
                email="closed@test.com", 
                name="Closed",
                account_status=AccountStatus.CLOSED
            )
            
            db.session.add_all([active_user, suspended_user, closed_user])
            db.session.commit()
            
            assert active_user.is_active()
            assert not suspended_user.is_active()
            assert not closed_user.is_active()
    
    def test_user_unique_constraints(self, app):
        """Test user unique constraints"""
        with app.app_context():
            user1 = User(microsoft_id="unique", email="user1@test.com", name="User 1")
            user2 = User(microsoft_id="unique", email="user2@test.com", name="User 2")
            
            db.session.add(user1)
            db.session.commit()
            
            db.session.add(user2)
            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()
    
    def test_user_string_representation(self, app):
        """Test user string representation"""
        with app.app_context():
            user = User(microsoft_id="test", email="test@test.com", name="Test User")
            assert str(user) == "Test User (test@test.com)"


class TestAccountModel:
    """Test cases for Account model"""
    
    def test_create_account(self, app):
        """Test creating a new account"""
        with app.app_context():
            user = User(microsoft_id="test", email="test@test.com", name="Test User")
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            assert account.id is not None
            assert account.user_id == user.id
            assert account.balance == Decimal('100.00')
            assert account.currency == 'GBP'
    
    def test_account_balance_validation(self, app):
        """Test account balance validation"""
        with app.app_context():
            user = User(microsoft_id="test", email="test@test.com", name="Test User")
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            
            # Test valid balance changes
            assert account.can_debit(Decimal('50.00'))
            assert account.can_debit(Decimal('350.00'))  # Within overdraft limit
            assert not account.can_debit(Decimal('400.00'))  # Exceeds overdraft limit
            
            # Test balance limits
            assert account.is_within_limits(Decimal('250.00'))
            assert account.is_within_limits(Decimal('-250.00'))
            assert not account.is_within_limits(Decimal('300.00'))
            assert not account.is_within_limits(Decimal('-300.00'))
    
    def test_account_balance_operations(self, app):
        """Test account balance operations"""
        with app.app_context():
            user = User(microsoft_id="test", email="test@test.com", name="Test User")
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Test credit
            account.credit(Decimal('25.00'))
            assert account.balance == Decimal('125.00')
            
            # Test debit
            account.debit(Decimal('50.00'))
            assert account.balance == Decimal('75.00')
            
            # Test overdraft warning
            account.balance = Decimal('-200.00')
            assert account.is_near_overdraft_limit()
    
    def test_account_relationship(self, app):
        """Test account-user relationship"""
        with app.app_context():
            user = User(microsoft_id="test", email="test@test.com", name="Test User")
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            assert account.user == user
            assert user.account == account


class TestTransactionModel:
    """Test cases for Transaction model"""
    
    def test_create_transfer_transaction(self, app):
        """Test creating a transfer transaction"""
        with app.app_context():
            sender = User(microsoft_id="sender", email="sender@test.com", name="Sender")
            recipient = User(microsoft_id="recipient", email="recipient@test.com", name="Recipient")
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                note='Test payment'
            )
            
            assert transaction.sender_id == sender.id
            assert transaction.recipient_id == recipient.id
            assert transaction.amount == Decimal('25.00')
            assert transaction.transaction_type == TransactionType.TRANSFER
            assert transaction.status == TransactionStatus.PENDING
            assert transaction.note == 'Test payment'
    
    def test_create_event_contribution(self, app):
        """Test creating an event contribution transaction"""
        with app.app_context():
            contributor = User(microsoft_id="contributor", email="contributor@test.com", name="Contributor")
            creator = User(microsoft_id="creator", email="creator@test.com", name="Creator")
            db.session.add_all([contributor, creator])
            db.session.flush()
            
            event = EventAccount(
                creator_id=creator.id,
                name="Test Event",
                description="Test event description"
            )
            db.session.add(event)
            db.session.flush()
            
            transaction = Transaction.create_event_contribution(
                contributor_id=contributor.id,
                event_id=event.id,
                amount=Decimal('30.00'),
                note='Happy to contribute!'
            )
            
            assert transaction.sender_id == contributor.id
            assert transaction.event_id == event.id
            assert transaction.amount == Decimal('30.00')
            assert transaction.transaction_type == TransactionType.EVENT_CONTRIBUTION
            assert transaction.note == 'Happy to contribute!'
    
    def test_transaction_status_changes(self, app):
        """Test transaction status changes"""
        with app.app_context():
            sender = User(microsoft_id="sender", email="sender@test.com", name="Sender")
            recipient = User(microsoft_id="recipient", email="recipient@test.com", name="Recipient")
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            
            assert transaction.status == TransactionStatus.PENDING
            assert transaction.processed_at is None
            
            # Mark as processed
            transaction.mark_as_processed()
            assert transaction.status == TransactionStatus.COMPLETED
            assert transaction.processed_at is not None
            
            # Test failed transaction
            failed_transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('50.00')
            )
            failed_transaction.mark_as_failed()
            assert failed_transaction.status == TransactionStatus.FAILED
    
    def test_transaction_validation(self, app):
        """Test transaction validation"""
        with app.app_context():
            sender = User(microsoft_id="sender", email="sender@test.com", name="Sender")
            recipient = User(microsoft_id="recipient", email="recipient@test.com", name="Recipient")
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            # Test valid transaction
            valid_transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            assert valid_transaction.is_valid()
            
            # Test invalid amount
            with pytest.raises(ValueError):
                Transaction.create_transfer(
                    sender_id=sender.id,
                    recipient_id=recipient.id,
                    amount=Decimal('-25.00')
                )
    
    def test_transaction_relationships(self, app):
        """Test transaction relationships"""
        with app.app_context():
            sender = User(microsoft_id="sender", email="sender@test.com", name="Sender")
            recipient = User(microsoft_id="recipient", email="recipient@test.com", name="Recipient")
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            transaction = Transaction.create_transfer(
                sender_id=sender.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00')
            )
            db.session.add(transaction)
            db.session.commit()
            
            assert transaction.sender == sender
            assert transaction.recipient == recipient


class TestEventAccountModel:
    """Test cases for EventAccount model"""
    
    def test_create_event_account(self, app):
        """Test creating an event account"""
        with app.app_context():
            creator = User(microsoft_id="creator", email="creator@test.com", name="Creator")
            db.session.add(creator)
            db.session.flush()
            
            event = EventAccount(
                creator_id=creator.id,
                name="Team Lunch",
                description="Monthly team lunch",
                target_amount=Decimal('200.00'),
                deadline=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(event)
            db.session.commit()
            
            assert event.id is not None
            assert event.creator_id == creator.id
            assert event.name == "Team Lunch"
            assert event.description == "Monthly team lunch"
            assert event.target_amount == Decimal('200.00')
            assert event.status == EventStatus.ACTIVE
    
    def test_event_status_changes(self, app):
        """Test event status changes"""
        with app.app_context():
            creator = User(microsoft_id="creator", email="creator@test.com", name="Creator")
            db.session.add(creator)
            db.session.flush()
            
            event = EventAccount(
                creator_id=creator.id,
                name="Test Event",
                description="Test description"
            )
            db.session.add(event)
            db.session.commit()
            
            assert event.is_active()
            assert not event.is_closed()
            
            # Close event
            event.close()
            assert event.status == EventStatus.CLOSED
            assert event.closed_at is not None
            assert not event.is_active()
            assert event.is_closed()
    
    def test_event_progress_calculation(self, app):
        """Test event progress calculation"""
        with app.app_context():
            creator = User(microsoft_id="creator", email="creator@test.com", name="Creator")
            contributor = User(microsoft_id="contributor", email="contributor@test.com", name="Contributor")
            db.session.add_all([creator, contributor])
            db.session.flush()
            
            event = EventAccount(
                creator_id=creator.id,
                name="Test Event",
                description="Test description",
                target_amount=Decimal('100.00')
            )
            db.session.add(event)
            db.session.flush()
            
            # Add contributions
            contribution1 = Transaction.create_event_contribution(
                contributor_id=contributor.id,
                event_id=event.id,
                amount=Decimal('30.00')
            )
            contribution1.mark_as_processed()
            
            contribution2 = Transaction.create_event_contribution(
                contributor_id=contributor.id,
                event_id=event.id,
                amount=Decimal('20.00')
            )
            contribution2.mark_as_processed()
            
            db.session.add_all([contribution1, contribution2])
            db.session.commit()
            
            # Test progress calculation
            progress = event.get_progress_percentage()
            assert progress == 50.0  # 50/100 = 50%
            
            total_contributions = event.get_total_contributions()
            assert total_contributions == Decimal('50.00')
    
    def test_event_deadline_validation(self, app):
        """Test event deadline validation"""
        with app.app_context():
            creator = User(microsoft_id="creator", email="creator@test.com", name="Creator")
            db.session.add(creator)
            db.session.flush()
            
            # Test future deadline (valid)
            future_event = EventAccount(
                creator_id=creator.id,
                name="Future Event",
                description="Event with future deadline",
                deadline=datetime.utcnow() + timedelta(days=7)
            )
            assert future_event.is_deadline_valid()
            
            # Test past deadline (invalid)
            past_event = EventAccount(
                creator_id=creator.id,
                name="Past Event",
                description="Event with past deadline",
                deadline=datetime.utcnow() - timedelta(days=1)
            )
            assert not past_event.is_deadline_valid()
    
    def test_event_relationships(self, app):
        """Test event relationships"""
        with app.app_context():
            creator = User(microsoft_id="creator", email="creator@test.com", name="Creator")
            db.session.add(creator)
            db.session.flush()
            
            event = EventAccount(
                creator_id=creator.id,
                name="Test Event",
                description="Test description"
            )
            db.session.add(event)
            db.session.commit()
            
            assert event.creator == creator


class TestMoneyRequestModel:
    """Test cases for MoneyRequest model"""
    
    def test_create_money_request(self, app):
        """Test creating a money request"""
        with app.app_context():
            requester = User(microsoft_id="requester", email="requester@test.com", name="Requester")
            recipient = User(microsoft_id="recipient", email="recipient@test.com", name="Recipient")
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            request = MoneyRequest(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('50.00'),
                note='Lunch money',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(request)
            db.session.commit()
            
            assert request.id is not None
            assert request.requester_id == requester.id
            assert request.recipient_id == recipient.id
            assert request.amount == Decimal('50.00')
            assert request.note == 'Lunch money'
            assert request.status == RequestStatus.PENDING
    
    def test_money_request_status_changes(self, app):
        """Test money request status changes"""
        with app.app_context():
            requester = User(microsoft_id="requester", email="requester@test.com", name="Requester")
            recipient = User(microsoft_id="recipient", email="recipient@test.com", name="Recipient")
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            request = MoneyRequest(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('50.00'),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(request)
            db.session.commit()
            
            assert request.is_pending()
            assert not request.is_approved()
            assert not request.is_declined()
            assert not request.is_expired()
            
            # Approve request
            request.approve()
            assert request.status == RequestStatus.APPROVED
            assert request.responded_at is not None
            assert request.is_approved()
            
            # Test declined request
            declined_request = MoneyRequest(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('25.00'),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            declined_request.decline()
            assert declined_request.status == RequestStatus.DECLINED
            assert declined_request.is_declined()
    
    def test_money_request_expiration(self, app):
        """Test money request expiration"""
        with app.app_context():
            requester = User(microsoft_id="requester", email="requester@test.com", name="Requester")
            recipient = User(microsoft_id="recipient", email="recipient@test.com", name="Recipient")
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            # Create expired request
            expired_request = MoneyRequest(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('50.00'),
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(expired_request)
            db.session.commit()
            
            assert expired_request.is_expired()
            
            # Mark as expired
            expired_request.mark_as_expired()
            assert expired_request.status == RequestStatus.EXPIRED
    
    def test_money_request_relationships(self, app):
        """Test money request relationships"""
        with app.app_context():
            requester = User(microsoft_id="requester", email="requester@test.com", name="Requester")
            recipient = User(microsoft_id="recipient", email="recipient@test.com", name="Recipient")
            db.session.add_all([requester, recipient])
            db.session.flush()
            
            request = MoneyRequest(
                requester_id=requester.id,
                recipient_id=recipient.id,
                amount=Decimal('50.00'),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(request)
            db.session.commit()
            
            assert request.requester == requester
            assert request.recipient == recipient


class TestAuditLogModel:
    """Test cases for AuditLog model"""
    
    def test_create_audit_log(self, app):
        """Test creating an audit log"""
        with app.app_context():
            user = User(microsoft_id="user", email="user@test.com", name="User")
            db.session.add(user)
            db.session.flush()
            
            audit_log = AuditLog(
                user_id=user.id,
                action=AuditAction.USER_LOGIN,
                entity_type='User',
                entity_id=user.id,
                details={'login_method': 'microsoft_sso'},
                ip_address='192.168.1.1',
                user_agent='Test Browser'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            assert audit_log.id is not None
            assert audit_log.user_id == user.id
            assert audit_log.action == AuditAction.USER_LOGIN
            assert audit_log.entity_type == 'User'
            assert audit_log.entity_id == user.id
            assert audit_log.details['login_method'] == 'microsoft_sso'
            assert audit_log.ip_address == '192.168.1.1'
    
    def test_audit_log_system_event(self, app):
        """Test creating system audit log"""
        with app.app_context():
            system_log = AuditLog(
                user_id=None,  # System events have no user
                action=AuditAction.SYSTEM_MAINTENANCE,
                entity_type='System',
                entity_id='system',
                details={'maintenance_type': 'backup'},
                ip_address='127.0.0.1'
            )
            db.session.add(system_log)
            db.session.commit()
            
            assert system_log.user_id is None
            assert system_log.action == AuditAction.SYSTEM_MAINTENANCE
            assert system_log.is_system_event()
    
    def test_audit_log_relationships(self, app):
        """Test audit log relationships"""
        with app.app_context():
            user = User(microsoft_id="user", email="user@test.com", name="User")
            db.session.add(user)
            db.session.flush()
            
            audit_log = AuditLog(
                user_id=user.id,
                action=AuditAction.USER_LOGIN,
                entity_type='User',
                entity_id=user.id,
                details={},
                ip_address='192.168.1.1'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            assert audit_log.user == user


class TestNotificationModel:
    """Test cases for Notification model"""
    
    def test_create_notification(self, app):
        """Test creating a notification"""
        with app.app_context():
            user = User(microsoft_id="user", email="user@test.com", name="User")
            db.session.add(user)
            db.session.flush()
            
            notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Payment Received',
                message='You received £25.00 from John Doe',
                data={'transaction_id': 'trans-123', 'amount': '25.00'}
            )
            db.session.add(notification)
            db.session.commit()
            
            assert notification.id is not None
            assert notification.recipient_id == user.id
            assert notification.notification_type == NotificationType.TRANSACTION_RECEIVED
            assert notification.title == 'Payment Received'
            assert notification.status == NotificationStatus.UNREAD
            assert notification.data['transaction_id'] == 'trans-123'
    
    def test_notification_status_changes(self, app):
        """Test notification status changes"""
        with app.app_context():
            user = User(microsoft_id="user", email="user@test.com", name="User")
            db.session.add(user)
            db.session.flush()
            
            notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.MONEY_REQUEST_RECEIVED,
                title='Money Request',
                message='Someone requested £15.00'
            )
            db.session.add(notification)
            db.session.commit()
            
            assert notification.is_unread()
            assert not notification.is_read()
            assert notification.read_at is None
            
            # Mark as read
            notification.mark_as_read()
            assert notification.status == NotificationStatus.READ
            assert notification.is_read()
            assert notification.read_at is not None
    
    def test_notification_relationships(self, app):
        """Test notification relationships"""
        with app.app_context():
            user = User(microsoft_id="user", email="user@test.com", name="User")
            db.session.add(user)
            db.session.flush()
            
            notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.SYSTEM_ALERT,
                title='System Alert',
                message='System maintenance scheduled'
            )
            db.session.add(notification)
            db.session.commit()
            
            assert notification.recipient == user


