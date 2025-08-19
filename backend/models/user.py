"""
User model for SoftBankCashWire application
"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from enum import Enum
from .base import db, generate_uuid, utc_now

class UserRole(Enum):
    """User role enumeration"""
    EMPLOYEE = "EMPLOYEE"
    ADMIN = "ADMIN"
    FINANCE = "FINANCE"

class AccountStatus(Enum):
    """Account status enumeration"""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"

class User(db.Model):
    """User model representing employees in the system"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    microsoft_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    account_status = Column(SQLEnum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sent_transactions = relationship("Transaction", foreign_keys="Transaction.sender_id", back_populates="sender")
    received_transactions = relationship("Transaction", foreign_keys="Transaction.recipient_id", back_populates="recipient")
    created_events = relationship("EventAccount", back_populates="creator")
    money_requests_sent = relationship("MoneyRequest", foreign_keys="MoneyRequest.requester_id", back_populates="requester")
    money_requests_received = relationship("MoneyRequest", foreign_keys="MoneyRequest.recipient_id", back_populates="recipient")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_microsoft_id', 'microsoft_id'),
        Index('idx_user_email', 'email'),
        Index('idx_user_role_status', 'role', 'account_status'),
    )
    
    def __repr__(self):
        return f'<User {self.name} ({self.email})>'
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'microsoft_id': self.microsoft_id,
            'email': self.email,
            'name': self.name,
            'role': self.role.value,
            'account_status': self.account_status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def is_active(self):
        """Check if user account is active"""
        return self.account_status == AccountStatus.ACTIVE
    
    def has_role(self, role):
        """Check if user has specific role"""
        if isinstance(role, str):
            role = UserRole(role)
        return self.role == role
    
    def can_access_admin_features(self):
        """Check if user can access admin features"""
        return self.role in [UserRole.ADMIN, UserRole.FINANCE]
    
    def can_access_finance_features(self):
        """Check if user can access finance features"""
        return self.role == UserRole.FINANCE