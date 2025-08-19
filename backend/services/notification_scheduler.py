"""
Notification scheduler service for SoftBankCashWire
Handles scheduled notifications like event deadline reminders
"""
from typing import List
from datetime import datetime, timedelta
from sqlalchemy import and_
from models import db, EventAccount, EventStatus, User
from services.notification_service import NotificationService
from services.audit_service import AuditService


class NotificationScheduler:
    """Service for scheduling and sending automated notifications"""
    
    @staticmethod
    def check_event_deadlines():
        """Check for events with approaching deadlines and send notifications"""
        try:
            # Get events with deadlines in the next 24 hours that are still active
            tomorrow = datetime.utcnow() + timedelta(days=1)
            today = datetime.utcnow()
            
            events_with_approaching_deadlines = db.session.query(EventAccount).filter(
                and_(
                    EventAccount.status == EventStatus.ACTIVE,
                    EventAccount.deadline.isnot(None),
                    EventAccount.deadline <= tomorrow,
                    EventAccount.deadline > today
                )
            ).all()
            
            notifications_sent = 0
            
            for event in events_with_approaching_deadlines:
                try:
                    # Get all contributors to this event
                    from services.event_service import EventService
                    contributors = EventService.get_event_contributors(event.id)
                    
                    # Notify event creator
                    NotificationService.notify_event_deadline_approaching(
                        user_id=event.creator_id,
                        event_name=event.name,
                        deadline=event.deadline.strftime('%Y-%m-%d %H:%M'),
                        event_id=event.id
                    )
                    notifications_sent += 1
                    
                    # Notify all contributors (except creator to avoid duplicate)
                    for contributor in contributors:
                        if contributor['user_id'] != event.creator_id:
                            NotificationService.notify_event_deadline_approaching(
                                user_id=contributor['user_id'],
                                event_name=event.name,
                                deadline=event.deadline.strftime('%Y-%m-%d %H:%M'),
                                event_id=event.id
                            )
                            notifications_sent += 1
                    
                except Exception as e:
                    # Log error but continue with other events
                    AuditService.log_system_event(
                        action_type='DEADLINE_NOTIFICATION_FAILED',
                        details={
                            'event_id': event.id,
                            'event_name': event.name,
                            'error': str(e)
                        }
                    )
            
            # Log the batch operation
            if notifications_sent > 0:
                AuditService.log_system_event(
                    action_type='DEADLINE_NOTIFICATIONS_SENT',
                    details={
                        'events_checked': len(events_with_approaching_deadlines),
                        'notifications_sent': notifications_sent
                    }
                )
            
            return notifications_sent
            
        except Exception as e:
            AuditService.log_system_event(
                action_type='DEADLINE_CHECK_FAILED',
                details={'error': str(e)}
            )
            raise Exception(f"Failed to check event deadlines: {str(e)}")
    
    @staticmethod
    def send_system_maintenance_notification(title: str, message: str, 
                                           scheduled_time: str = None):
        """Send system maintenance notification to all active users"""
        try:
            active_users = db.session.query(User).filter(
                User.account_status == 'ACTIVE'
            ).all()
            
            notifications_sent = 0
            for user in active_users:
                NotificationService.notify_system_maintenance(
                    user_id=user.id,
                    title=title,
                    message=message,
                    scheduled_time=scheduled_time
                )
                notifications_sent += 1
            
            AuditService.log_system_event(
                action_type='MAINTENANCE_NOTIFICATIONS_SENT',
                details={
                    'title': title,
                    'recipients_count': notifications_sent,
                    'scheduled_time': scheduled_time
                }
            )
            
            return notifications_sent
            
        except Exception as e:
            raise Exception(f"Failed to send maintenance notifications: {str(e)}")
    
    @staticmethod
    def send_security_alert(title: str, message: str, target_users: List[str] = None):
        """Send security alert to specific users or all users"""
        try:
            if target_users:
                # Send to specific users
                users = db.session.query(User).filter(
                    and_(
                        User.id.in_(target_users),
                        User.account_status == 'ACTIVE'
                    )
                ).all()
            else:
                # Send to all active users
                users = db.session.query(User).filter(
                    User.account_status == 'ACTIVE'
                ).all()
            
            notifications_sent = 0
            for user in users:
                NotificationService.notify_security_alert(
                    user_id=user.id,
                    title=title,
                    message=message,
                    alert_data={
                        'timestamp': datetime.utcnow().isoformat(),
                        'severity': 'HIGH'
                    }
                )
                notifications_sent += 1
            
            AuditService.log_system_event(
                action_type='SECURITY_ALERTS_SENT',
                details={
                    'title': title,
                    'recipients_count': notifications_sent,
                    'target_users': target_users
                }
            )
            
            return notifications_sent
            
        except Exception as e:
            raise Exception(f"Failed to send security alerts: {str(e)}")
    
    @staticmethod
    def cleanup_old_notifications(days_old: int = 30):
        """Clean up old read notifications to keep database size manageable"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete old read notifications
            from models import Notification
            deleted_count = db.session.query(Notification).filter(
                and_(
                    Notification.read == True,
                    Notification.created_at < cutoff_date
                )
            ).delete()
            
            db.session.commit()
            
            AuditService.log_system_event(
                action_type='OLD_NOTIFICATIONS_CLEANED',
                details={
                    'deleted_count': deleted_count,
                    'cutoff_date': cutoff_date.isoformat()
                }
            )
            
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to cleanup old notifications: {str(e)}")