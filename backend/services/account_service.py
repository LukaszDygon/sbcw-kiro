"""
Account management service for SoftBankCashWire
Handles account operations, balance management, and transaction history
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func
from models import (
    db, User, Account, Transaction, TransactionType, TransactionStatus,
    AuditLog, generate_uuid
)

class AccountService:
    """Service for managing user accounts and balances"""
    
    # Account limits
    MIN_BALANCE = Decimal('-250.00')
    MAX_BALANCE = Decimal('250.00')
    OVERDRAFT_WARNING_THRESHOLD = Decimal('50.00')
    
    @classmethod
    def get_account_by_user_id(cls, user_id: str) -> Optional[Account]:
        """
        Get account by user ID
        
        Args:
            user_id: User ID
            
        Returns:
            Account object or None if not found
        """
        return Account.query.filter_by(user_id=user_id).first()
    
    @classmethod
    def get_account_balance(cls, user_id: str) -> Decimal:
        """
        Get current account balance for user
        
        Args:
            user_id: User ID
            
        Returns:
            Current balance as Decimal
            
        Raises:
            ValueError: If account not found
        """
        account = cls.get_account_by_user_id(user_id)
        
        if not account:
            raise ValueError(f"Account not found for user {user_id}")
        
        return account.balance
    
    @classmethod
    def validate_transaction_limits(cls, user_id: str, amount: Decimal) -> Dict[str, Any]:
        """
        Validate if transaction amount is within account limits
        
        Args:
            user_id: User ID
            amount: Transaction amount (positive for credit, negative for debit)
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValueError: If account not found
        """
        account = cls.get_account_by_user_id(user_id)
        
        if not account:
            raise ValueError(f"Account not found for user {user_id}")
        
        current_balance = account.balance
        new_balance = current_balance + amount
        
        validation_result = {
            'valid': True,
            'current_balance': current_balance,
            'new_balance': new_balance,
            'amount': amount,
            'warnings': [],
            'errors': []
        }
        
        # Check minimum balance (overdraft limit)
        if new_balance < cls.MIN_BALANCE:
            validation_result['valid'] = False
            validation_result['errors'].append({
                'code': 'INSUFFICIENT_FUNDS',
                'message': f'Transaction would exceed overdraft limit. Available: {cls.get_available_balance(user_id)}'
            })
        
        # Check maximum balance
        if new_balance > cls.MAX_BALANCE:
            validation_result['valid'] = False
            validation_result['errors'].append({
                'code': 'BALANCE_LIMIT_EXCEEDED',
                'message': f'Transaction would exceed maximum balance of {cls.MAX_BALANCE}'
            })
        
        # Check for overdraft warning
        if amount < 0 and new_balance <= cls.OVERDRAFT_WARNING_THRESHOLD and new_balance >= cls.MIN_BALANCE:
            validation_result['warnings'].append({
                'code': 'APPROACHING_OVERDRAFT',
                'message': f'Balance will be {new_balance}, approaching overdraft limit'
            })
        
        return validation_result
    
    @classmethod
    def get_available_balance(cls, user_id: str) -> Decimal:
        """
        Get available balance including overdraft
        
        Args:
            user_id: User ID
            
        Returns:
            Available balance including overdraft
        """
        current_balance = cls.get_account_balance(user_id)
        return current_balance - cls.MIN_BALANCE
    
    @classmethod
    def update_account_balance(cls, user_id: str, amount: Decimal, 
                              transaction_id: str = None, 
                              ip_address: str = None, 
                              user_agent: str = None) -> Dict[str, Any]:
        """
        Update account balance with validation and audit logging
        
        Args:
            user_id: User ID
            amount: Amount to add/subtract from balance
            transaction_id: Associated transaction ID for audit
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with update results
            
        Raises:
            ValueError: If validation fails or account not found
        """
        account = cls.get_account_by_user_id(user_id)
        
        if not account:
            raise ValueError(f"Account not found for user {user_id}")
        
        # Validate transaction limits
        validation = cls.validate_transaction_limits(user_id, amount)
        
        if not validation['valid']:
            error_messages = [error['message'] for error in validation['errors']]
            raise ValueError(f"Transaction validation failed: {'; '.join(error_messages)}")
        
        # Store old balance for audit
        old_balance = account.balance
        
        try:
            # Update balance
            new_balance = account.update_balance(amount)
            
            # Log balance change
            AuditLog.log_account_change(
                account=account,
                user_id=user_id,
                old_balance=old_balance,
                new_balance=new_balance,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Add transaction reference if provided
            if transaction_id:
                AuditLog.log_user_action(
                    user_id=user_id,
                    action_type='BALANCE_UPDATED_BY_TRANSACTION',
                    entity_type='Account',
                    entity_id=account.id,
                    old_values={'balance': str(old_balance), 'transaction_id': transaction_id},
                    new_values={'balance': str(new_balance), 'transaction_id': transaction_id},
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            db.session.commit()
            
            return {
                'success': True,
                'old_balance': old_balance,
                'new_balance': new_balance,
                'amount': amount,
                'warnings': validation['warnings']
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to update balance: {str(e)}")
    
    @classmethod
    def get_transaction_history(cls, user_id: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get transaction history for user with filtering and pagination
        
        Args:
            user_id: User ID
            filters: Optional filters dictionary
                - start_date: Start date for filtering
                - end_date: End date for filtering
                - transaction_type: Filter by transaction type
                - category: Filter by category
                - min_amount: Minimum amount filter
                - max_amount: Maximum amount filter
                - page: Page number (default: 1)
                - per_page: Items per page (default: 20)
                - sort_by: Sort field (default: 'created_at')
                - sort_order: Sort order 'asc' or 'desc' (default: 'desc')
                
        Returns:
            Dictionary with transactions and pagination info
        """
        if filters is None:
            filters = {}
        
        # Base query for transactions where user is sender or recipient
        query = Transaction.query.filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            )
        )
        
        # Apply filters
        if filters.get('start_date'):
            query = query.filter(Transaction.created_at >= filters['start_date'])
        
        if filters.get('end_date'):
            query = query.filter(Transaction.created_at <= filters['end_date'])
        
        if filters.get('transaction_type'):
            query = query.filter(Transaction.transaction_type == filters['transaction_type'])
        
        if filters.get('category'):
            query = query.filter(Transaction.category.ilike(f"%{filters['category']}%"))
        
        if filters.get('min_amount'):
            query = query.filter(Transaction.amount >= Decimal(str(filters['min_amount'])))
        
        if filters.get('max_amount'):
            query = query.filter(Transaction.amount <= Decimal(str(filters['max_amount'])))
        
        # Search term filter (search in notes, recipient names, sender names)
        if filters.get('search_term'):
            search_term = filters['search_term']
            search_pattern = f'%{search_term}%'
            # Create aliases for sender and recipient users
            sender_user = db.aliased(User)
            recipient_user = db.aliased(User)
            
            query = query.outerjoin(sender_user, Transaction.sender_id == sender_user.id)
            query = query.outerjoin(recipient_user, Transaction.recipient_id == recipient_user.id)
            
            query = query.filter(
                or_(
                    Transaction.note.ilike(search_pattern),
                    Transaction.category.ilike(search_pattern),
                    sender_user.name.ilike(search_pattern),
                    recipient_user.name.ilike(search_pattern),
                    sender_user.email.ilike(search_pattern),
                    recipient_user.email.ilike(search_pattern)
                )
            )
        
        # Status filter
        if filters.get('status'):
            try:
                status = TransactionStatus(filters['status'].upper())
                query = query.filter(Transaction.status == status)
            except ValueError:
                pass  # Ignore invalid status values
        
        # Apply sorting
        sort_by = filters.get('sort_by', 'created_at')
        sort_order = filters.get('sort_order', 'desc')
        
        if hasattr(Transaction, sort_by):
            sort_column = getattr(Transaction, sort_by)
            if sort_order.lower() == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(desc(Transaction.created_at))
        
        # Apply pagination
        page = filters.get('page', 1)
        per_page = min(filters.get('per_page', 20), 100)  # Max 100 items per page
        
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Format transactions with additional info
        transactions = []
        for transaction in paginated.items:
            transaction_dict = transaction.to_dict(include_names=True)
            
            # Add direction indicator for user
            if transaction.sender_id == user_id:
                transaction_dict['direction'] = 'outgoing'
                transaction_dict['other_party_id'] = transaction.recipient_id or transaction.event_id
                transaction_dict['other_party_name'] = (
                    transaction.recipient.name if transaction.recipient 
                    else transaction.event_account.name if transaction.event_account 
                    else 'Unknown'
                )
            else:
                transaction_dict['direction'] = 'incoming'
                transaction_dict['other_party_id'] = transaction.sender_id
                transaction_dict['other_party_name'] = transaction.sender.name if transaction.sender else 'Unknown'
            
            transactions.append(transaction_dict)
        
        return {
            'transactions': transactions,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_prev': paginated.has_prev,
                'has_next': paginated.has_next,
                'prev_num': paginated.prev_num,
                'next_num': paginated.next_num
            }
        }
    
    @classmethod
    def get_account_summary(cls, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive account summary for user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with account summary information
        """
        account = cls.get_account_by_user_id(user_id)
        
        if not account:
            raise ValueError(f"Account not found for user {user_id}")
        
        # Get basic account info
        current_balance = account.balance
        available_balance = cls.get_available_balance(user_id)
        
        # Calculate transaction statistics
        thirty_days_ago = datetime.now(datetime.UTC) - timedelta(days=30)
        
        # Total transactions in last 30 days
        recent_transactions = Transaction.query.filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.created_at >= thirty_days_ago,
            Transaction.status == TransactionStatus.COMPLETED
        ).all()
        
        # Calculate spending and receiving
        total_sent = sum(
            t.amount for t in recent_transactions 
            if t.sender_id == user_id
        ) or Decimal('0.00')
        
        total_received = sum(
            t.amount for t in recent_transactions 
            if t.recipient_id == user_id
        ) or Decimal('0.00')
        
        # Get transaction counts by type
        transfer_count = len([
            t for t in recent_transactions 
            if t.transaction_type == TransactionType.TRANSFER
        ])
        
        event_contribution_count = len([
            t for t in recent_transactions 
            if t.transaction_type == TransactionType.EVENT_CONTRIBUTION and t.sender_id == user_id
        ])
        
        # Check for warnings
        warnings = []
        if current_balance <= cls.OVERDRAFT_WARNING_THRESHOLD:
            warnings.append({
                'code': 'LOW_BALANCE',
                'message': f'Account balance is low: {current_balance}'
            })
        
        if current_balance < Decimal('0.00'):
            warnings.append({
                'code': 'OVERDRAFT',
                'message': f'Account is in overdraft: {current_balance}'
            })
        
        return {
            'account_id': account.id,
            'user_id': user_id,
            'current_balance': str(current_balance),
            'available_balance': str(available_balance),
            'currency': account.currency,
            'account_limits': {
                'minimum_balance': str(cls.MIN_BALANCE),
                'maximum_balance': str(cls.MAX_BALANCE),
                'overdraft_limit': str(abs(cls.MIN_BALANCE))
            },
            'recent_activity': {
                'period_days': 30,
                'total_sent': str(total_sent),
                'total_received': str(total_received),
                'net_change': str(total_received - total_sent),
                'transaction_count': len(recent_transactions),
                'transfer_count': transfer_count,
                'event_contribution_count': event_contribution_count
            },
            'warnings': warnings,
            'created_at': account.created_at.isoformat() if account.created_at else None,
            'updated_at': account.updated_at.isoformat() if account.updated_at else None
        }
    
    @classmethod
    def get_spending_analytics(cls, user_id: str, period_days: int = 30) -> Dict[str, Any]:
        """
        Get spending analytics for user
        
        Args:
            user_id: User ID
            period_days: Analysis period in days
            
        Returns:
            Dictionary with spending analytics
        """
        start_date = datetime.now(datetime.UTC) - timedelta(days=period_days)
        
        # Get transactions where user is sender
        transactions = Transaction.query.filter(
            Transaction.sender_id == user_id,
            Transaction.created_at >= start_date,
            Transaction.status == TransactionStatus.COMPLETED
        ).all()
        
        # Group by category
        category_spending = {}
        for transaction in transactions:
            category = transaction.category or 'Uncategorized'
            if category not in category_spending:
                category_spending[category] = {
                    'total_amount': Decimal('0.00'),
                    'transaction_count': 0,
                    'transactions': []
                }
            
            category_spending[category]['total_amount'] += transaction.amount
            category_spending[category]['transaction_count'] += 1
            category_spending[category]['transactions'].append({
                'id': transaction.id,
                'amount': str(transaction.amount),
                'recipient_name': (
                    transaction.recipient.name if transaction.recipient
                    else transaction.event_account.name if transaction.event_account
                    else 'Unknown'
                ),
                'note': transaction.note,
                'created_at': transaction.created_at.isoformat()
            })
        
        # Convert to list and sort by amount
        categories = [
            {
                'category': category,
                'total_amount': str(data['total_amount']),
                'transaction_count': data['transaction_count'],
                'average_amount': str(data['total_amount'] / data['transaction_count']) if data['transaction_count'] > 0 else '0.00',
                'transactions': data['transactions']
            }
            for category, data in category_spending.items()
        ]
        
        categories.sort(key=lambda x: Decimal(x['total_amount']), reverse=True)
        
        # Calculate totals
        total_spent = sum(Decimal(cat['total_amount']) for cat in categories)
        total_transactions = sum(cat['transaction_count'] for cat in categories)
        
        return {
            'period_days': period_days,
            'start_date': start_date.isoformat(),
            'end_date': datetime.now(datetime.UTC).isoformat(),
            'total_spent': str(total_spent),
            'total_transactions': total_transactions,
            'average_transaction': str(total_spent / total_transactions) if total_transactions > 0 else '0.00',
            'categories': categories
        }
    
    @classmethod
    def check_account_status(cls, user_id: str) -> Dict[str, Any]:
        """
        Check account status and health
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with account status information
        """
        account = cls.get_account_by_user_id(user_id)
        user = User.query.get(user_id)
        
        if not account or not user:
            return {
                'status': 'NOT_FOUND',
                'message': 'Account or user not found'
            }
        
        status_info = {
            'account_status': 'HEALTHY',
            'user_status': user.account_status.value,
            'balance_status': 'NORMAL',
            'issues': [],
            'recommendations': []
        }
        
        # Check user account status
        if not user.is_active():
            status_info['account_status'] = 'INACTIVE'
            status_info['issues'].append('User account is not active')
        
        # Check balance status
        current_balance = account.balance
        
        if current_balance < Decimal('0.00'):
            status_info['balance_status'] = 'OVERDRAFT'
            status_info['issues'].append(f'Account is in overdraft: {current_balance}')
            status_info['recommendations'].append('Consider adding funds to your account')
        elif current_balance <= cls.OVERDRAFT_WARNING_THRESHOLD:
            status_info['balance_status'] = 'LOW'
            status_info['issues'].append(f'Account balance is low: {current_balance}')
            status_info['recommendations'].append('Monitor your spending to avoid overdraft')
        
        # Check for recent activity
        recent_transactions = Transaction.query.filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.created_at >= datetime.now(datetime.UTC) - timedelta(days=7)
        ).count()
        
        if recent_transactions == 0:
            status_info['recommendations'].append('No recent activity - consider using the system for transactions')
        
        return status_info