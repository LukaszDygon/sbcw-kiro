"""
Tests for NotificationService
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from services.notification_service import NotificationService
from models import (
    db, User, UserRole, AccountStatus, Account, 
    Notification, NotificationType, NotificationStatus
)

class TestNotificationService:
    """Test cases for NotificationService"""
    
    def test_create_transaction_notification(self, app):
        """Test creating transaction notification"""
        with app.app_context():
            # Create users
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.commit()
            
            # Test notification creation
            notification = NotificationService.create_transaction_notification(
                recipient_id=recipient.id,
                sender_name='Sender',
                amount=Decimal('25.00'),
                transaction_id='trans-123',
                note='Test payment'
            )
            
            assert notification.recipient_id == recipient.id
            assert notification.notification_type == NotificationType.TRANSACTION_RECEIVED
            assert notification.status == NotificationStatus.UNREAD
            assert 'Sender' in notification.title
            assert '25.00' in notification.message
            assert notification.data['transaction_id'] == 'trans-123'
            assert notification.data['amount'] == '25.00'
    
    def test_create_money_request_notification(self, app):
        """Test creating money request notification"""
        with app.app_context():
            # Create users
            requester = User(microsoft_id='requester', email='requester@test.com', name='Requester')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([requester, recipient])
            db.session.commit()
            
            # Test notification creation
            notification = NotificationService.create_money_request_notification(
                recipient_id=recipient.id,
                requester_name='Requester',
                amount=Decimal('50.00'),
                request_id='req-123',
                note='Lunch money'
            )
            
            assert notification.recipient_id == recipient.id
            assert notification.notification_type == NotificationType.MONEY_REQUEST_RECEIVED
            assert notification.status == NotificationStatus.UNREAD
            assert 'Requester' in notification.title
            assert '50.00' in notification.message
            assert notification.data['request_id'] == 'req-123'
            assert notification.data['amount'] == '50.00'
    
    def test_create_event_contribution_notification(self, app):
        """Test creating event contribution notification"""
        with app.app_context():
            # Create users
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            contributor = User(microsoft_id='contributor', email='contributor@test.com', name='Contributor')
            db.session.add_all([creator, contributor])
            db.session.commit()
            
            # Test notification creation
            notification = NotificationService.create_event_contribution_notification(
                recipient_id=creator.id,
                contributor_name='Contributor',
                event_name='Team Lunch',
                amount=Decimal('30.00'),
                event_id='event-123'
            )
            
            assert notification.recipient_id == creator.id
            assert notification.notification_type == NotificationType.EVENT_CONTRIBUTION
            assert notification.status == NotificationStatus.UNREAD
            assert 'Contributor' in notification.title
            assert 'Team Lunch' in notification.message
            assert '30.00' in notification.message
            assert notification.data['event_id'] == 'event-123'
    
    def test_create_event_deadline_notification(self, app):
        """Test creating event deadline notification"""
        with app.app_context():
            # Create user
            creator = User(microsoft_id='creator', email='creator@test.com', name='Creator')
            db.session.add(creator)
            db.session.commit()
            
            # Test notification creation
            deadline = datetime.now(datetime.UTC) + timedelta(days=1)
            notification = NotificationService.create_event_deadline_notification(
                recipient_id=creator.id,
                event_name='Team Party',
                deadline=deadline,
                event_id='event-456'
            )
            
            assert notification.recipient_id == creator.id
            assert notification.notification_type == NotificationType.EVENT_DEADLINE
            assert notification.status == NotificationStatus.UNREAD
            assert 'Team Party' in notification.title
            assert 'deadline' in notification.message.lower()
            assert notification.data['event_id'] == 'event-456'
    
    def test_create_system_notification(self, app):
        """Test creating system notification"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Test notification creation
            notification = NotificationService.create_system_notification(
                recipient_id=user.id,
                title='System Maintenance',
                message='System will be down for maintenance tonight',
                notification_type=NotificationType.SYSTEM_ALERT
            )
            
            assert notification.recipient_id == user.id
            assert notification.notification_type == NotificationType.SYSTEM_ALERT
            assert notification.status == NotificationStatus.UNREAD
            assert notification.title == 'System Maintenance'
            assert 'maintenance' in notification.message
    
    def test_get_user_notifications(self, app):
        """Test getting user notifications"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create notifications
            notification1 = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Payment Received',
                message='You received £25.00',
                status=NotificationStatus.UNREAD
            )
            notification2 = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.MONEY_REQUEST_RECEIVED,
                title='Money Request',
                message='Someone requested £15.00',
                status=NotificationStatus.READ
            )
            db.session.add_all([notification1, notification2])
            db.session.commit()
            
            # Test getting all notifications
            all_notifications = NotificationService.get_user_notifications(user.id)
            assert len(all_notifications) == 2
            
            # Test getting unread notifications only
            unread_notifications = NotificationService.get_user_notifications(
                user.id, 
                unread_only=True
            )
            assert len(unread_notifications) == 1
            assert unread_notifications[0]['status'] == NotificationStatus.UNREAD.value
            
            # Test pagination
            paginated = NotificationService.get_user_notifications(
                user.id, 
                limit=1, 
                offset=0
            )
            assert len(paginated) == 1
    
    def test_mark_notification_as_read(self, app):
        """Test marking notification as read"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create notification
            notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Payment Received',
                message='You received £25.00',
                status=NotificationStatus.UNREAD
            )
            db.session.add(notification)
            db.session.commit()
            
            # Test marking as read
            result = NotificationService.mark_notification_as_read(
                notification_id=notification.id,
                user_id=user.id
            )
            
            assert result['success'] is True
            
            # Verify status changed
            updated_notification = Notification.query.get(notification.id)
            assert updated_notification.status == NotificationStatus.READ
            assert updated_notification.read_at is not None
    
    def test_mark_notification_as_read_unauthorized(self, app):
        """Test marking notification as read by unauthorized user"""
        with app.app_context():
            # Create users
            owner = User(microsoft_id='owner', email='owner@test.com', name='Owner')
            other_user = User(microsoft_id='other', email='other@test.com', name='Other')
            db.session.add_all([owner, other_user])
            db.session.commit()
            
            # Create notification for owner
            notification = Notification(
                recipient_id=owner.id,
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Payment Received',
                message='You received £25.00',
                status=NotificationStatus.UNREAD
            )
            db.session.add(notification)
            db.session.commit()
            
            # Test unauthorized access
            with pytest.raises(ValueError, match="Notification not found or access denied"):
                NotificationService.mark_notification_as_read(
                    notification_id=notification.id,
                    user_id=other_user.id
                )
    
    def test_mark_all_notifications_as_read(self, app):
        """Test marking all notifications as read"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create multiple notifications
            notifications = []
            for i in range(3):
                notification = Notification(
                    recipient_id=user.id,
                    notification_type=NotificationType.TRANSACTION_RECEIVED,
                    title=f'Payment {i+1}',
                    message=f'You received £{10+i}.00',
                    status=NotificationStatus.UNREAD
                )
                notifications.append(notification)
            
            db.session.add_all(notifications)
            db.session.commit()
            
            # Test marking all as read
            result = NotificationService.mark_all_notifications_as_read(user.id)
            
            assert result['success'] is True
            assert result['updated_count'] == 3
            
            # Verify all are marked as read
            updated_notifications = Notification.query.filter_by(recipient_id=user.id).all()
            for notification in updated_notifications:
                assert notification.status == NotificationStatus.READ
                assert notification.read_at is not None
    
    def test_delete_notification(self, app):
        """Test deleting notification"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create notification
            notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Payment Received',
                message='You received £25.00',
                status=NotificationStatus.READ
            )
            db.session.add(notification)
            db.session.commit()
            
            notification_id = notification.id
            
            # Test deletion
            result = NotificationService.delete_notification(
                notification_id=notification_id,
                user_id=user.id
            )
            
            assert result['success'] is True
            
            # Verify deletion
            deleted_notification = Notification.query.get(notification_id)
            assert deleted_notification is None
    
    def test_delete_notification_unauthorized(self, app):
        """Test deleting notification by unauthorized user"""
        with app.app_context():
            # Create users
            owner = User(microsoft_id='owner', email='owner@test.com', name='Owner')
            other_user = User(microsoft_id='other', email='other@test.com', name='Other')
            db.session.add_all([owner, other_user])
            db.session.commit()
            
            # Create notification for owner
            notification = Notification(
                recipient_id=owner.id,
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Payment Received',
                message='You received £25.00',
                status=NotificationStatus.READ
            )
            db.session.add(notification)
            db.session.commit()
            
            # Test unauthorized deletion
            with pytest.raises(ValueError, match="Notification not found or access denied"):
                NotificationService.delete_notification(
                    notification_id=notification.id,
                    user_id=other_user.id
                )
    
    def test_get_notification_count(self, app):
        """Test getting notification count"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create notifications
            unread_notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Payment 1',
                message='You received £25.00',
                status=NotificationStatus.UNREAD
            )
            read_notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.MONEY_REQUEST_RECEIVED,
                title='Request 1',
                message='Someone requested £15.00',
                status=NotificationStatus.READ
            )
            db.session.add_all([unread_notification, read_notification])
            db.session.commit()
            
            # Test getting counts
            counts = NotificationService.get_notification_count(user.id)
            
            assert counts['total'] == 2
            assert counts['unread'] == 1
            assert counts['read'] == 1
    
    def test_cleanup_old_notifications(self, app):
        """Test cleaning up old notifications"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create old notification
            old_notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Old Payment',
                message='You received £25.00',
                status=NotificationStatus.READ
            )
            # Manually set old created_at date
            old_notification.created_at = datetime.now(datetime.UTC) - timedelta(days=95)
            
            # Create recent notification
            recent_notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.MONEY_REQUEST_RECEIVED,
                title='Recent Request',
                message='Someone requested £15.00',
                status=NotificationStatus.UNREAD
            )
            
            db.session.add_all([old_notification, recent_notification])
            db.session.commit()
            
            # Test cleanup
            result = NotificationService.cleanup_old_notifications(days=90)
            
            assert result['success'] is True
            assert result['deleted_count'] == 1
            
            # Verify old notification was deleted
            remaining_notifications = Notification.query.filter_by(recipient_id=user.id).all()
            assert len(remaining_notifications) == 1
            assert remaining_notifications[0].title == 'Recent Request'
    
    def test_send_bulk_notifications(self, app):
        """Test sending bulk notifications"""
        with app.app_context():
            # Create users
            user1 = User(microsoft_id='user1', email='user1@test.com', name='User 1')
            user2 = User(microsoft_id='user2', email='user2@test.com', name='User 2')
            user3 = User(microsoft_id='user3', email='user3@test.com', name='User 3')
            db.session.add_all([user1, user2, user3])
            db.session.commit()
            
            # Test bulk notification
            recipient_ids = [user1.id, user2.id, user3.id]
            result = NotificationService.send_bulk_notifications(
                recipient_ids=recipient_ids,
                title='System Maintenance',
                message='System will be down for maintenance tonight',
                notification_type=NotificationType.SYSTEM_ALERT
            )
            
            assert result['success'] is True
            assert result['sent_count'] == 3
            
            # Verify notifications were created
            notifications = Notification.query.filter(
                Notification.recipient_id.in_(recipient_ids)
            ).all()
            assert len(notifications) == 3
            
            for notification in notifications:
                assert notification.title == 'System Maintenance'
                assert notification.notification_type == NotificationType.SYSTEM_ALERT
                assert notification.status == NotificationStatus.UNREAD
    
    def test_get_notifications_by_type(self, app):
        """Test getting notifications by type"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='user', email='user@test.com', name='User')
            db.session.add(user)
            db.session.commit()
            
            # Create different types of notifications
            transaction_notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Payment Received',
                message='You received £25.00',
                status=NotificationStatus.UNREAD
            )
            request_notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.MONEY_REQUEST_RECEIVED,
                title='Money Request',
                message='Someone requested £15.00',
                status=NotificationStatus.UNREAD
            )
            system_notification = Notification(
                recipient_id=user.id,
                notification_type=NotificationType.SYSTEM_ALERT,
                title='System Alert',
                message='System maintenance scheduled',
                status=NotificationStatus.UNREAD
            )
            db.session.add_all([transaction_notification, request_notification, system_notification])
            db.session.commit()
            
            # Test getting transaction notifications
            transaction_notifications = NotificationService.get_notifications_by_type(
                user.id, 
                NotificationType.TRANSACTION_RECEIVED
            )
            assert len(transaction_notifications) == 1
            assert transaction_notifications[0]['title'] == 'Payment Received'
            
            # Test getting system notifications
            system_notifications = NotificationService.get_notifications_by_type(
                user.id, 
                NotificationType.SYSTEM_ALERT
            )
            assert len(system_notifications) == 1
            assert system_notifications[0]['title'] == 'System Alert'