"""
Money Request model for SoftBankCashWire application
"""
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum as SQLEnum, CheckConstraint, Index
from sqlalchemy.orm import relationship
from enum import Enum
from decimal import Decimal
from datetime import timedelta
from .base import db, generate_uuid, utc_now

class RequestStatus(Enum):
    """Money request status enumeration"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"

class MoneyRequest(db.Model):
    """Money Request model representing payment requests between users"""
    __tablename__ = 'money_requests'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    requester_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    recipient_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    note = Column(String(500), nullable=True)
    status = Column(SQLEnum(RequestStatus), nullable=False, default=RequestStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    responded_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], back_populates="money_requests_sent")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="money_requests_received")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_money_request_positive_amount'),
        CheckConstraint('requester_id != recipient_id', name='ck_money_request_different_users'),
        Index('idx_money_request_requester_created', 'requester_id', 'created_at'),
        Index('idx_money_request_recipient_status', 'recipient_id', 'status'),
        Index('idx_money_request_status_expires', 'status', 'expires_at'),
        Index('idx_money_request_expires', 'expires_at'),
    )
    
    def __init__(self, **kwargs):
        """Initialize money request with default expiration"""
        super().__init__(**kwargs)
        if not self.expires_at:
            # Default expiration: 7 days from creation
            self.expires_at = self.created_at + timedelta(days=7)
    
    def __repr__(self):
        return f'<MoneyRequest {self.requester_id} -> {self.recipient_id}: {self.amount}>'
    
    def to_dict(self, include_names=False):
        """Convert money request to dictionary for API responses"""
        result = {
            'id': self.id,
            'requester_id': self.requester_id,
            'recipient_id': self.recipient_id,
            'amount': str(self.amount),
            'note': self.note,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
        
        if include_names:
            result['requester_name'] = self.requester.name if self.requester else None
            result['recipient_name'] = self.recipient.name if self.recipient else None
        
        return result
    
    def is_pending(self):
        """Check if request is pending"""
        return self.status == RequestStatus.PENDING
    
    def is_approved(self):
        """Check if request is approved"""
        return self.status == RequestStatus.APPROVED
    
    def is_declined(self):
        """Check if request is declined"""
        return self.status == RequestStatus.DECLINED
    
    def is_expired(self):
        """Check if request is expired"""
        return self.status == RequestStatus.EXPIRED or utc_now() > self.expires_at
    
    def can_be_responded_to(self):
        """Check if request can still be approved or declined"""
        return self.is_pending() and not self.is_expired()
    
    def approve(self):
        """Approve the money request"""
        if not self.can_be_responded_to():
            raise ValueError("Cannot approve expired or already responded request")
        
        self.status = RequestStatus.APPROVED
        self.responded_at = utc_now()
    
    def decline(self):
        """Decline the money request"""
        if not self.can_be_responded_to():
            raise ValueError("Cannot decline expired or already responded request")
        
        self.status = RequestStatus.DECLINED
        self.responded_at = utc_now()
    
    def expire(self):
        """Mark request as expired"""
        if self.is_pending():
            self.status = RequestStatus.EXPIRED
            self.responded_at = utc_now()
    
    def get_time_until_expiry(self):
        """Get time remaining until expiry"""
        if self.is_expired():
            return timedelta(0)
        
        return self.expires_at - utc_now()
    
    def is_expiring_soon(self, hours=24):
        """Check if request is expiring within specified hours"""
        if not self.is_pending():
            return False
        
        time_until_expiry = self.get_time_until_expiry()
        return time_until_expiry <= timedelta(hours=hours)
    
    @classmethod
    def create_request(cls, requester_id, recipient_id, amount, note=None, expires_in_days=7):
        """Create a new money request"""
        if requester_id == recipient_id:
            raise ValueError("Cannot create money request to yourself")
        
        expires_at = utc_now() + timedelta(days=expires_in_days)
        
        return cls(
            requester_id=requester_id,
            recipient_id=recipient_id,
            amount=Decimal(str(amount)),
            note=note,
            expires_at=expires_at
        )
    
    @classmethod
    def get_pending_requests_for_user(cls, user_id):
        """Get all pending requests for a user"""
        return cls.query.filter(
            cls.recipient_id == user_id,
            cls.status == RequestStatus.PENDING,
            cls.expires_at > utc_now()
        ).all()
    
    @classmethod
    def get_expired_requests(cls):
        """Get all requests that should be marked as expired"""
        return cls.query.filter(
            cls.status == RequestStatus.PENDING,
            cls.expires_at <= utc_now()
        ).all()