"""
Notification service for SoftBankCashWire
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from models import db, Notification, NotificationType, NotificationPriority, User
from services.audit_service import AuditService


class NotificationService:
    """Service for managing user notifications"""
    
    @staticmethod
    def create_notification(user_id: str, notification_type: NotificationType,
                          title: str, message: str, priority: NotificationPriority = NotificationPriority.MEDIUM,
                          data: Dict[str, Any] = None, expires_in_days: int = None) -> Notification:
        """Create a new notification"""
        try:
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                data=data,
                expires_in_days=expires_in_days
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # Log the notification creation
            AuditService.log_user_action(
                user_id=user_id,
                action_type='NOTIFICATION_CREATED',
                entity_type='Notification',
                entity_id=notification.id,
                new_values={
                    'notification_id': notification.id,
                    'type': notification_type.value,
                    'priority': priority.value
                }
            )
            
            return notification
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create notification: {str(e)}")
    
    @staticmethod
    def get_user_notifications(user_id: str, unread_only: bool = False, 
                             limit: int = 50, offset: int = 0) -> List[Notification]:
        """Get notifications for a user"""
        try:
            query = db.session.query(Notification).filter(
                Notification.user_id == user_id
            )
            
            if unread_only:
                query = query.filter(Notification.read == False)
            
            # Filter out expired notifications
            query = query.filter(
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.utcnow()
                )
            )
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).limit(limit).offset(offset).all()
            
            return notifications
            
        except Exception as e:
            raise Exception(f"Failed to get user notifications: {str(e)}")
    
    @staticmethod
    def mark_notification_as_read(notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            notification = db.session.query(Notification).filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()
            
            if not notification:
                return False
            
            notification.mark_as_read()
            db.session.commit()
            
            # Log the action
            AuditService.log_user_action(
                user_id=user_id,
                action='NOTIFICATION_READ',
                details={'notification_id': notification_id}
            )
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to mark notification as read: {str(e)}")
    
    @staticmethod
    def mark_all_notifications_as_read(user_id: str) -> int:
        """Mark all notifications as read for a user"""
        try:
            count = db.session.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.read == False
                )
            ).update({'read': True})
            
            db.session.commit()
            
            # Log the action
            AuditService.log_user_action(
                user_id=user_id,
                action='ALL_NOTIFICATIONS_READ',
                details={'count': count}
            )
            
            return count
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to mark all notifications as read: {str(e)}")
    
    @staticmethod
    def delete_notification(notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        try:
            notification = db.session.query(Notification).filter(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            ).first()
            
            if not notification:
                return False
            
            db.session.delete(notification)
            db.session.commit()
            
            # Log the action
            AuditService.log_user_action(
                user_id=user_id,
                action='NOTIFICATION_DELETED',
                details={'notification_id': notification_id}
            )
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to delete notification: {str(e)}")
    
    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """Get count of unread notifications for a user"""
        try:
            count = db.session.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.read == False,
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at > datetime.utcnow()
                    )
                )
            ).count()
            
            return count
            
        except Exception as e:
            raise Exception(f"Failed to get unread count: {str(e)}")
    
    @staticmethod
    def cleanup_expired_notifications() -> int:
        """Clean up expired notifications"""
        try:
            count = db.session.query(Notification).filter(
                and_(
                    Notification.expires_at.isnot(None),
                    Notification.expires_at < datetime.utcnow()
                )
            ).delete()
            
            db.session.commit()
            
            # Log the cleanup
            AuditService.log_system_event(
                action_type='NOTIFICATION_CLEANUP',
                details={'deleted_count': count}
            )
            
            return count
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to cleanup expired notifications: {str(e)}")
    
    # Convenience methods for creating specific types of notifications
    
    @staticmethod
    def notify_transaction_received(user_id: str, amount: str, sender_name: str, 
                                  transaction_id: str) -> Notification:
        """Create notification for received transaction"""
        notification = NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.TRANSACTION_RECEIVED,
            title="Money Received",
            message=f"You received £{amount} from {sender_name}",
            priority=NotificationPriority.MEDIUM,
            data={
                'amount': amount,
                'sender_name': sender_name,
                'transaction_id': transaction_id
            }
        )
        NotificationService._trigger_real_time_notification(user_id, notification)
        return notification
    
    @staticmethod
    def notify_transaction_sent(user_id: str, amount: str, recipient_name: str, 
                              transaction_id: str) -> Notification:
        """Create notification for sent transaction"""
        return NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.TRANSACTION_SENT,
            title="Money Sent",
            message=f"You sent £{amount} to {recipient_name}",
            priority=NotificationPriority.LOW,
            data={
                'amount': amount,
                'recipient_name': recipient_name,
                'transaction_id': transaction_id
            }
        )
    
    @staticmethod
    def notify_money_request_received(user_id: str, amount: str, requester_name: str, 
                                    request_id: str) -> Notification:
        """Create notification for received money request"""
        notification = NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.MONEY_REQUEST_RECEIVED,
            title="Money Request Received",
            message=f"{requester_name} is requesting £{amount} from you",
            priority=NotificationPriority.HIGH,
            data={
                'amount': amount,
                'requester_name': requester_name,
                'request_id': request_id
            },
            expires_in_days=30
        )
        NotificationService._trigger_real_time_notification(user_id, notification)
        return notification
    
    @staticmethod
    def notify_money_request_approved(user_id: str, amount: str, approver_name: str, 
                                    request_id: str) -> Notification:
        """Create notification for approved money request"""
        return NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.MONEY_REQUEST_APPROVED,
            title="Money Request Approved",
            message=f"{approver_name} approved your request for £{amount}",
            priority=NotificationPriority.MEDIUM,
            data={
                'amount': amount,
                'approver_name': approver_name,
                'request_id': request_id
            }
        )
    
    @staticmethod
    def notify_money_request_declined(user_id: str, amount: str, decliner_name: str, 
                                    request_id: str) -> Notification:
        """Create notification for declined money request"""
        return NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.MONEY_REQUEST_DECLINED,
            title="Money Request Declined",
            message=f"{decliner_name} declined your request for £{amount}",
            priority=NotificationPriority.MEDIUM,
            data={
                'amount': amount,
                'decliner_name': decliner_name,
                'request_id': request_id
            }
        )
    
    @staticmethod
    def notify_event_contribution(user_id: str, event_name: str, amount: str, 
                                contributor_name: str, event_id: str) -> Notification:
        """Create notification for event contribution"""
        return NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.EVENT_CONTRIBUTION,
            title="Event Contribution",
            message=f"{contributor_name} contributed £{amount} to {event_name}",
            priority=NotificationPriority.LOW,
            data={
                'event_name': event_name,
                'amount': amount,
                'contributor_name': contributor_name,
                'event_id': event_id
            },
            expires_in_days=7
        )
    
    @staticmethod
    def notify_event_deadline_approaching(user_id: str, event_name: str, 
                                        deadline: str, event_id: str) -> Notification:
        """Create notification for approaching event deadline"""
        notification = NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.EVENT_DEADLINE_APPROACHING,
            title="Event Deadline Approaching",
            message=f"The deadline for {event_name} is approaching ({deadline})",
            priority=NotificationPriority.HIGH,
            data={
                'event_name': event_name,
                'deadline': deadline,
                'event_id': event_id
            },
            expires_in_days=1
        )
        NotificationService._trigger_real_time_notification(user_id, notification)
        return notification
    
    @staticmethod
    def notify_event_closed(user_id: str, event_name: str, event_id: str) -> Notification:
        """Create notification for closed event"""
        return NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.EVENT_CLOSED,
            title="Event Closed",
            message=f"The event {event_name} has been closed",
            priority=NotificationPriority.MEDIUM,
            data={
                'event_name': event_name,
                'event_id': event_id
            },
            expires_in_days=7
        )
    
    @staticmethod
    def notify_system_maintenance(user_id: str, title: str, message: str, 
                                scheduled_time: str = None) -> Notification:
        """Create notification for system maintenance"""
        data = {}
        if scheduled_time:
            data['scheduled_time'] = scheduled_time
        
        notification = NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.SYSTEM_MAINTENANCE,
            title=title,
            message=message,
            priority=NotificationPriority.HIGH,
            data=data,
            expires_in_days=3
        )
        NotificationService._trigger_real_time_notification(user_id, notification)
        return notification
    
    @staticmethod
    def notify_security_alert(user_id: str, title: str, message: str, 
                            alert_data: Dict[str, Any] = None) -> Notification:
        """Create notification for security alert"""
        notification = NotificationService.create_notification(
            user_id=user_id,
            notification_type=NotificationType.SECURITY_ALERT,
            title=title,
            message=message,
            priority=NotificationPriority.URGENT,
            data=alert_data or {},
            expires_in_days=7
        )
        NotificationService._trigger_real_time_notification(user_id, notification)
        return notification
    
    @staticmethod
    def broadcast_notification_to_all_users(notification_type: NotificationType,
                                          title: str, message: str, 
                                          priority: NotificationPriority = NotificationPriority.MEDIUM,
                                          data: Dict[str, Any] = None,
                                          expires_in_days: int = None) -> int:
        """Broadcast a notification to all active users"""
        try:
            # Get all active users
            active_users = db.session.query(User).filter(
                User.account_status == 'ACTIVE'
            ).all()
            
            notifications_created = 0
            for user in active_users:
                notification = NotificationService.create_notification(
                    user_id=user.id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    priority=priority,
                    data=data,
                    expires_in_days=expires_in_days
                )
                
                # Trigger real-time notification
                NotificationService._trigger_real_time_notification(user.id, notification)
                notifications_created += 1
            
            # Log the broadcast
            AuditService.log_system_event(
                action_type='NOTIFICATION_BROADCAST',
                details={
                    'type': notification_type.value,
                    'title': title,
                    'recipients_count': notifications_created
                }
            )
            
            return notifications_created
            
        except Exception as e:
            raise Exception(f"Failed to broadcast notification: {str(e)}")
    
    @staticmethod
    def _trigger_real_time_notification(user_id: str, notification: Notification):
        """Trigger real-time notification for a user"""
        try:
            # In a production environment, you would use a message queue (Redis, RabbitMQ)
            # or WebSocket connections to push notifications to connected clients
            # For now, we'll store the notification in a way that can be polled
            
            # This is a simplified implementation
            # In practice, you'd use Redis pub/sub or similar
            pass
            
        except Exception as e:
            # Don't fail the notification creation if real-time delivery fails
            AuditService.log_system_event(
                action_type='REAL_TIME_NOTIFICATION_FAILED',
                details={
                    'user_id': user_id,
                    'notification_id': notification.id,
                    'error': str(e)
                }
            )