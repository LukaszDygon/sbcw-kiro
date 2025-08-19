"""
Audit Log model for SoftBankCashWire application
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from .base import db, generate_uuid, utc_now
import json
import enum

class AuditAction(enum.Enum):
    """Audit action enumeration"""
    LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    LOGIN_FAILED = 'LOGIN_FAILED'
    LOGOUT = 'LOGOUT'
    TRANSACTION_CREATED = 'TRANSACTION_CREATED'
    TRANSACTION_FAILED = 'TRANSACTION_FAILED'
    ACCOUNT_BALANCE_CHANGED = 'ACCOUNT_BALANCE_CHANGED'
    MONEY_REQUEST_CREATED = 'MONEY_REQUEST_CREATED'
    MONEY_REQUEST_APPROVED = 'MONEY_REQUEST_APPROVED'
    MONEY_REQUEST_DECLINED = 'MONEY_REQUEST_DECLINED'
    EVENT_CREATED = 'EVENT_CREATED'
    EVENT_CONTRIBUTION = 'EVENT_CONTRIBUTION'
    EVENT_CLOSED = 'EVENT_CLOSED'
    USER_CREATED = 'USER_CREATED'
    USER_UPDATED = 'USER_UPDATED'
    USER_DEACTIVATED = 'USER_DEACTIVATED'
    SYSTEM_BACKUP = 'SYSTEM_BACKUP'
    SYSTEM_MAINTENANCE = 'SYSTEM_MAINTENANCE'
    SECURITY_ALERT = 'SECURITY_ALERT'

class AuditLog(db.Model):
    """Audit Log model for tracking all system activities"""
    __tablename__ = 'audit_logs'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True)  # Nullable for system events
    action_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(36), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_action_created', 'action_type', 'created_at'),
        Index('idx_audit_entity_created', 'entity_type', 'entity_id', 'created_at'),
        Index('idx_audit_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<AuditLog {self.action_type} on {self.entity_type} by {self.user_id}>'
    
    def to_dict(self, include_user_name=False):
        """Convert audit log to dictionary for API responses"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_user_name and self.user:
            result['user_name'] = self.user.name
        
        return result
    
    def get_changes(self):
        """Get a summary of changes made"""
        if not self.old_values or not self.new_values:
            return None
        
        changes = {}
        old_vals = self.old_values if isinstance(self.old_values, dict) else {}
        new_vals = self.new_values if isinstance(self.new_values, dict) else {}
        
        # Find changed fields
        all_keys = set(old_vals.keys()) | set(new_vals.keys())
        
        for key in all_keys:
            old_val = old_vals.get(key)
            new_val = new_vals.get(key)
            
            if old_val != new_val:
                changes[key] = {
                    'old': old_val,
                    'new': new_val
                }
        
        return changes if changes else None
    
    @classmethod
    def log_user_action(cls, user_id, action_type, entity_type, entity_id=None, 
                       old_values=None, new_values=None, ip_address=None, user_agent=None):
        """Log a user action"""
        log_entry = cls(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.add(log_entry)
        return log_entry
    
    @classmethod
    def log_system_event(cls, action_type, entity_type, entity_id=None, details=None):
        """Log a system event (no user associated)"""
        log_entry = cls(
            user_id=None,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values=details
        )
        
        db.session.add(log_entry)
        return log_entry
    
    @classmethod
    def log_transaction(cls, transaction, user_id=None, ip_address=None, user_agent=None):
        """Log a transaction event"""
        transaction_data = {
            'id': transaction.id,
            'sender_id': transaction.sender_id,
            'recipient_id': transaction.recipient_id,
            'event_id': transaction.event_id,
            'amount': str(transaction.amount),
            'transaction_type': transaction.transaction_type.value,
            'status': transaction.status.value
        }
        
        return cls.log_user_action(
            user_id=user_id or transaction.sender_id,
            action_type='TRANSACTION_CREATED',
            entity_type='Transaction',
            entity_id=transaction.id,
            new_values=transaction_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_login(cls, user_id, ip_address=None, user_agent=None, success=True):
        """Log a login attempt"""
        action_type = 'LOGIN_SUCCESS' if success else 'LOGIN_FAILED'
        
        return cls.log_user_action(
            user_id=user_id,
            action_type=action_type,
            entity_type='User',
            entity_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_account_change(cls, account, user_id, old_balance, new_balance, 
                          ip_address=None, user_agent=None):
        """Log an account balance change"""
        old_values = {'balance': str(old_balance)}
        new_values = {'balance': str(new_balance)}
        
        return cls.log_user_action(
            user_id=user_id,
            action_type='ACCOUNT_BALANCE_CHANGED',
            entity_type='Account',
            entity_id=account.id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_event_action(cls, event_account, user_id, action_type, 
                        ip_address=None, user_agent=None):
        """Log an event account action"""
        event_data = {
            'id': event_account.id,
            'name': event_account.name,
            'status': event_account.status.value,
            'total_contributions': str(event_account.total_contributions)
        }
        
        return cls.log_user_action(
            user_id=user_id,
            action_type=action_type,
            entity_type='EventAccount',
            entity_id=event_account.id,
            new_values=event_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_money_request_action(cls, money_request, user_id, action_type,
                                ip_address=None, user_agent=None):
        """Log a money request action"""
        request_data = {
            'id': money_request.id,
            'requester_id': money_request.requester_id,
            'recipient_id': money_request.recipient_id,
            'amount': str(money_request.amount),
            'status': money_request.status.value
        }
        
        return cls.log_user_action(
            user_id=user_id,
            action_type=action_type,
            entity_type='MoneyRequest',
            entity_id=money_request.id,
            new_values=request_data,
            ip_address=ip_address,
            user_agent=user_agent
        )