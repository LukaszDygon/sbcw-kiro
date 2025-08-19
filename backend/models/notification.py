"""
Notification model for SoftBankCashWire
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import db
import uuid
import enum


class NotificationType(enum.Enum):
    """Notification type enumeration"""
    TRANSACTION_RECEIVED = 'TRANSACTION_RECEIVED'
    TRANSACTION_SENT = 'TRANSACTION_SENT'
    MONEY_REQUEST_RECEIVED = 'MONEY_REQUEST_RECEIVED'
    MONEY_REQUEST_APPROVED = 'MONEY_REQUEST_APPROVED'
    MONEY_REQUEST_DECLINED = 'MONEY_REQUEST_DECLINED'
    EVENT_CONTRIBUTION = 'EVENT_CONTRIBUTION'
    EVENT_DEADLINE_APPROACHING = 'EVENT_DEADLINE_APPROACHING'
    EVENT_CLOSED = 'EVENT_CLOSED'
    SYSTEM_MAINTENANCE = 'SYSTEM_MAINTENANCE'
    SECURITY_ALERT = 'SECURITY_ALERT'


class NotificationPriority(enum.Enum):
    """Notification priority enumeration"""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    URGENT = 'URGENT'


class NotificationStatus(enum.Enum):
    """Notification status enumeration"""
    UNREAD = 'UNREAD'
    READ = 'READ'
    ARCHIVED = 'ARCHIVED'


class Notification(db.Model):
    """Notification model for user notifications"""
    
    __tablename__ = 'notifications'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(SQLEnum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)
    read = Column(Boolean, nullable=False, default=False)
    data = Column(JSON, nullable=True)  # Additional data for the notification
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    def __init__(self, user_id: str, notification_type: NotificationType, title: str, 
                 message: str, priority: NotificationPriority = NotificationPriority.MEDIUM,
                 data: dict = None, expires_in_days: int = None):
        """Initialize notification"""
        self.user_id = user_id
        self.type = notification_type
        self.title = title
        self.message = message
        self.priority = priority
        self.data = data or {}
        
        if expires_in_days:
            self.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.read = True
    
    def is_expired(self) -> bool:
        """Check if notification is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> dict:
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value,
            'title': self.title,
            'message': self.message,
            'priority': self.priority.value,
            'read': self.read,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def create_transaction_notification(cls, user_id: str, transaction_type: str, 
                                      amount: str, other_party: str, is_sender: bool = False):
        """Create a transaction-related notification"""
        if is_sender:
            title = "Money Sent"
            message = f"You sent £{amount} to {other_party}"
            notification_type = NotificationType.TRANSACTION_SENT
        else:
            title = "Money Received"
            message = f"You received £{amount} from {other_party}"
            notification_type = NotificationType.TRANSACTION_RECEIVED
        
        return cls(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            data={'amount': amount, 'other_party': other_party}
        )
    
    @classmethod
    def create_money_request_notification(cls, user_id: str, request_type: str, 
                                        amount: str, other_party: str, request_id: str):
        """Create a money request notification"""
        if request_type == 'received':
            title = "Money Request Received"
            message = f"{other_party} is requesting £{amount} from you"
            notification_type = NotificationType.MONEY_REQUEST_RECEIVED
            priority = NotificationPriority.HIGH
        elif request_type == 'approved':
            title = "Money Request Approved"
            message = f"{other_party} approved your request for £{amount}"
            notification_type = NotificationType.MONEY_REQUEST_APPROVED
            priority = NotificationPriority.MEDIUM
        else:  # declined
            title = "Money Request Declined"
            message = f"{other_party} declined your request for £{amount}"
            notification_type = NotificationType.MONEY_REQUEST_DECLINED
            priority = NotificationPriority.MEDIUM
        
        return cls(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            data={'amount': amount, 'other_party': other_party, 'request_id': request_id},
            expires_in_days=30
        )
    
    @classmethod
    def create_event_notification(cls, user_id: str, event_type: str, event_name: str, 
                                amount: str = None, contributor: str = None):
        """Create an event-related notification"""
        if event_type == 'contribution':
            title = "Event Contribution"
            message = f"{contributor} contributed £{amount} to {event_name}"
            notification_type = NotificationType.EVENT_CONTRIBUTION
            priority = NotificationPriority.LOW
        elif event_type == 'deadline_approaching':
            title = "Event Deadline Approaching"
            message = f"The deadline for {event_name} is approaching"
            notification_type = NotificationType.EVENT_DEADLINE_APPROACHING
            priority = NotificationPriority.HIGH
        else:  # closed
            title = "Event Closed"
            message = f"The event {event_name} has been closed"
            notification_type = NotificationType.EVENT_CLOSED
            priority = NotificationPriority.MEDIUM
        
        data = {'event_name': event_name}
        if amount:
            data['amount'] = amount
        if contributor:
            data['contributor'] = contributor
        
        return cls(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            data=data,
            expires_in_days=7
        )
    
    @classmethod
    def create_system_notification(cls, user_id: str, notification_type: str, 
                                 title: str, message: str):
        """Create a system notification"""
        if notification_type == 'maintenance':
            notification_type = NotificationType.SYSTEM_MAINTENANCE
            priority = NotificationPriority.HIGH
        else:  # security_alert
            notification_type = NotificationType.SECURITY_ALERT
            priority = NotificationPriority.URGENT
        
        return cls(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            expires_in_days=3
        )