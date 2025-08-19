"""
Event Account model for SoftBankCashWire application
"""
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum as SQLEnum, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum
from decimal import Decimal
from .base import db, generate_uuid, utc_now

class EventStatus(Enum):
    """Event status enumeration"""
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class EventAccount(db.Model):
    """Event Account model representing collective funding events"""
    __tablename__ = 'event_accounts'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    creator_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=False)
    target_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(SQLEnum(EventStatus), nullable=False, default=EventStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    closed_at = Column(DateTime, nullable=True)
    
    # Relationships
    creator = relationship("User", back_populates="created_events")
    contributions = relationship("Transaction", back_populates="event_account", cascade="all, delete-orphan")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('target_amount IS NULL OR target_amount > 0', name='ck_event_positive_target'),
        CheckConstraint('deadline IS NULL OR deadline > created_at', name='ck_event_future_deadline'),
        Index('idx_event_creator_created', 'creator_id', 'created_at'),
        Index('idx_event_status_created', 'status', 'created_at'),
        Index('idx_event_deadline', 'deadline'),
        Index('idx_event_name', 'name'),
    )
    
    def __repr__(self):
        return f'<EventAccount {self.name} by {self.creator_id}>'
    
    @hybrid_property
    def total_contributions(self):
        """Calculate total contributions to this event"""
        from .transaction import TransactionStatus
        return sum(
            contribution.amount for contribution in self.contributions
            if contribution.status == TransactionStatus.COMPLETED
        ) or Decimal('0.00')
    
    def to_dict(self, include_creator_name=False, include_contributions=False):
        """Convert event account to dictionary for API responses"""
        result = {
            'id': self.id,
            'creator_id': self.creator_id,
            'name': self.name,
            'description': self.description,
            'target_amount': str(self.target_amount) if self.target_amount else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status.value,
            'total_contributions': str(self.total_contributions),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }
        
        if include_creator_name and self.creator:
            result['creator_name'] = self.creator.name
        
        if include_contributions:
            result['contributions'] = [
                {
                    'contributor_id': contrib.sender_id,
                    'contributor_name': contrib.sender.name if contrib.sender else None,
                    'amount': str(contrib.amount),
                    'created_at': contrib.created_at.isoformat() if contrib.created_at else None,
                    'note': contrib.note
                }
                for contrib in self.contributions
                if contrib.is_completed()
            ]
        
        return result
    
    def is_active(self):
        """Check if event is active"""
        return self.status == EventStatus.ACTIVE
    
    def is_closed(self):
        """Check if event is closed"""
        return self.status == EventStatus.CLOSED
    
    def is_cancelled(self):
        """Check if event is cancelled"""
        return self.status == EventStatus.CANCELLED
    
    def can_receive_contributions(self):
        """Check if event can receive new contributions"""
        return self.status == EventStatus.ACTIVE
    
    def has_deadline_passed(self):
        """Check if event deadline has passed"""
        if not self.deadline:
            return False
        return utc_now() > self.deadline
    
    def get_progress_percentage(self):
        """Get progress percentage towards target (if target is set)"""
        if not self.target_amount or self.target_amount <= 0:
            return None
        
        progress = (self.total_contributions / self.target_amount) * 100
        return min(progress, 100)  # Cap at 100%
    
    def get_remaining_amount(self):
        """Get remaining amount to reach target (if target is set)"""
        if not self.target_amount:
            return None
        
        remaining = self.target_amount - self.total_contributions
        return max(remaining, Decimal('0.00'))
    
    def close_event(self):
        """Close the event account"""
        self.status = EventStatus.CLOSED
        self.closed_at = utc_now()
    
    def cancel_event(self):
        """Cancel the event account"""
        self.status = EventStatus.CANCELLED
        self.closed_at = utc_now()
    
    def get_contributor_count(self):
        """Get number of unique contributors"""
        from .transaction import TransactionStatus
        contributor_ids = set(
            contrib.sender_id for contrib in self.contributions
            if contrib.status == TransactionStatus.COMPLETED
        )
        return len(contributor_ids)
    
    def get_contributions_by_user(self, user_id):
        """Get all contributions by a specific user"""
        from .transaction import TransactionStatus
        return [
            contrib for contrib in self.contributions
            if contrib.sender_id == user_id and contrib.status == TransactionStatus.COMPLETED
        ]
    
    def user_total_contribution(self, user_id):
        """Get total contribution amount by a specific user"""
        contributions = self.get_contributions_by_user(user_id)
        return sum(contrib.amount for contrib in contributions) or Decimal('0.00')