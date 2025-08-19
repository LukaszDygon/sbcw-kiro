"""
Account model for SoftBankCashWire application
"""
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from decimal import Decimal
from .base import db, generate_uuid, utc_now

class Account(db.Model):
    """Account model representing user financial accounts"""
    __tablename__ = 'accounts'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True)
    balance = Column(Numeric(precision=10, scale=2), nullable=False, default=Decimal('0.00'))
    currency = Column(String(3), nullable=False, default='GBP')
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="account")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('balance >= -250.00', name='ck_account_min_balance'),
        CheckConstraint('balance <= 250.00', name='ck_account_max_balance'),
        Index('idx_account_user_id', 'user_id'),
        Index('idx_account_balance', 'balance'),
    )
    
    def __repr__(self):
        return f'<Account {self.user_id}: {self.balance} {self.currency}>'
    
    def to_dict(self):
        """Convert account to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'balance': str(self.balance),
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def has_sufficient_funds(self, amount):
        """Check if account has sufficient funds for a transaction"""
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        return (self.balance - amount) >= Decimal('-250.00')
    
    def would_exceed_limit(self, amount):
        """Check if adding amount would exceed maximum balance"""
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        return (self.balance + amount) > Decimal('250.00')
    
    def is_approaching_overdraft(self, threshold=Decimal('50.00')):
        """Check if account is approaching overdraft limit"""
        return self.balance <= threshold
    
    def get_available_balance(self):
        """Get available balance including overdraft"""
        return self.balance + Decimal('250.00')
    
    def update_balance(self, amount):
        """Update account balance with validation"""
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        
        new_balance = self.balance + amount
        
        # Validate balance limits
        if new_balance < Decimal('-250.00'):
            raise ValueError(f"Transaction would exceed overdraft limit. Current: {self.balance}, Change: {amount}")
        
        if new_balance > Decimal('250.00'):
            raise ValueError(f"Transaction would exceed maximum balance. Current: {self.balance}, Change: {amount}")
        
        self.balance = new_balance
        self.updated_at = utc_now()
        
        return self.balance