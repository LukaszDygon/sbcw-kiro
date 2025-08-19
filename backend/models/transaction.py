"""
Transaction model for SoftBankCashWire application
"""
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Enum as SQLEnum, CheckConstraint, Index
from sqlalchemy.orm import relationship
from enum import Enum
from decimal import Decimal
from .base import db, generate_uuid, utc_now

class TransactionType(Enum):
    """Transaction type enumeration"""
    TRANSFER = "TRANSFER"
    EVENT_CONTRIBUTION = "EVENT_CONTRIBUTION"

class TransactionStatus(Enum):
    """Transaction status enumeration"""
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Transaction(db.Model):
    """Transaction model representing money transfers"""
    __tablename__ = 'transactions'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    sender_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    recipient_id = Column(String(36), ForeignKey('users.id'), nullable=True)  # Nullable for event contributions
    event_id = Column(String(36), ForeignKey('event_accounts.id'), nullable=True)  # For event contributions
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, default=TransactionType.TRANSFER)
    category = Column(String(100), nullable=True)
    note = Column(String(500), nullable=True)
    status = Column(SQLEnum(TransactionStatus), nullable=False, default=TransactionStatus.COMPLETED)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_transactions")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_transactions")
    event_account = relationship("EventAccount", back_populates="contributions")
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_transaction_positive_amount'),
        CheckConstraint(
            "(transaction_type = 'TRANSFER' AND recipient_id IS NOT NULL AND event_id IS NULL) OR "
            "(transaction_type = 'EVENT_CONTRIBUTION' AND event_id IS NOT NULL)",
            name='ck_transaction_type_consistency'
        ),
        Index('idx_transaction_sender_created', 'sender_id', 'created_at'),
        Index('idx_transaction_recipient_created', 'recipient_id', 'created_at'),
        Index('idx_transaction_event_created', 'event_id', 'created_at'),
        Index('idx_transaction_type_status', 'transaction_type', 'status'),
        Index('idx_transaction_category', 'category'),
    )
    
    def __repr__(self):
        if self.transaction_type == TransactionType.TRANSFER:
            return f'<Transaction {self.sender_id} -> {self.recipient_id}: {self.amount}>'
        else:
            return f'<EventContribution {self.sender_id} -> Event {self.event_id}: {self.amount}>'
    
    def to_dict(self, include_names=False):
        """Convert transaction to dictionary for API responses"""
        result = {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'event_id': self.event_id,
            'amount': str(self.amount),
            'transaction_type': self.transaction_type.value,
            'category': self.category,
            'note': self.note,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
        
        if include_names:
            result['sender_name'] = self.sender.name if self.sender else None
            result['recipient_name'] = self.recipient.name if self.recipient else None
            result['event_name'] = self.event_account.name if self.event_account else None
        
        return result
    
    def is_transfer(self):
        """Check if transaction is a peer-to-peer transfer"""
        return self.transaction_type == TransactionType.TRANSFER
    
    def is_event_contribution(self):
        """Check if transaction is an event contribution"""
        return self.transaction_type == TransactionType.EVENT_CONTRIBUTION
    
    def is_completed(self):
        """Check if transaction is completed"""
        return self.status == TransactionStatus.COMPLETED
    
    def mark_as_processed(self):
        """Mark transaction as processed"""
        self.processed_at = utc_now()
        self.status = TransactionStatus.COMPLETED
    
    def mark_as_failed(self):
        """Mark transaction as failed"""
        self.status = TransactionStatus.FAILED
        self.processed_at = utc_now()
    
    @classmethod
    def create_transfer(cls, sender_id, recipient_id, amount, category=None, note=None):
        """Create a peer-to-peer transfer transaction"""
        return cls(
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=Decimal(str(amount)),
            transaction_type=TransactionType.TRANSFER,
            category=category,
            note=note
        )
    
    @classmethod
    def create_event_contribution(cls, sender_id, event_id, amount, note=None):
        """Create an event contribution transaction"""
        return cls(
            sender_id=sender_id,
            event_id=event_id,
            amount=Decimal(str(amount)),
            transaction_type=TransactionType.EVENT_CONTRIBUTION,
            category="Event Contribution",
            note=note
        )