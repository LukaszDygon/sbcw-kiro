"""
Transaction processing service for SoftBankCashWire
Handles peer-to-peer transfers, bulk transfers, and transaction validation
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import and_, or_, desc
from models import (
    db, User, Account, Transaction, TransactionType, TransactionStatus,
    EventAccount, EventStatus, AuditLog, generate_uuid
)
from services.account_service import AccountService
from services.notification_service import NotificationService

class TransactionService:
    """Service for processing financial transactions"""
    
    @classmethod
    def send_money(cls, sender_id: str, recipient_id: str, amount: Decimal, 
                   category: str = None, note: str = None,
                   ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Send money from one user to another
        
        Args:
            sender_id: ID of the sender
            recipient_id: ID of the recipient
            amount: Amount to transfer
            category: Optional transaction category
            note: Optional transaction note
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with transaction result
            
        Raises:
            ValueError: If validation fails or transaction cannot be processed
        """
        # Validate inputs
        if sender_id == recipient_id:
            raise ValueError("Cannot send money to yourself")
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Validate users exist and are active
        sender = User.query.get(sender_id)
        recipient = User.query.get(recipient_id)
        
        if not sender or not sender.is_active():
            raise ValueError("Sender account not found or inactive")
        
        if not recipient or not recipient.is_active():
            raise ValueError("Recipient account not found or inactive")
        
        # Get accounts
        sender_account = AccountService.get_account_by_user_id(sender_id)
        recipient_account = AccountService.get_account_by_user_id(recipient_id)
        
        if not sender_account or not recipient_account:
            raise ValueError("Account not found for sender or recipient")
        
        # Validate transaction limits for sender (debit)
        sender_validation = AccountService.validate_transaction_limits(sender_id, -amount)
        if not sender_validation['valid']:
            error_messages = [error['message'] for error in sender_validation['errors']]
            raise ValueError(f"Sender validation failed: {'; '.join(error_messages)}")
        
        # Validate transaction limits for recipient (credit)
        recipient_validation = AccountService.validate_transaction_limits(recipient_id, amount)
        if not recipient_validation['valid']:
            error_messages = [error['message'] for error in recipient_validation['errors']]
            raise ValueError(f"Recipient validation failed: {'; '.join(error_messages)}")
        
        # Create transaction record
        transaction = Transaction.create_transfer(
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=amount,
            category=category,
            note=note
        )
        
        try:
            # Start database transaction
            db.session.add(transaction)
            db.session.flush()  # Get transaction ID
            
            # Update balances atomically
            sender_result = AccountService.update_account_balance(
                user_id=sender_id,
                amount=-amount,
                transaction_id=transaction.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            recipient_result = AccountService.update_account_balance(
                user_id=recipient_id,
                amount=amount,
                transaction_id=transaction.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Mark transaction as processed
            transaction.mark_as_processed()
            
            # Log transaction
            AuditLog.log_transaction(
                transaction=transaction,
                user_id=sender_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Commit all changes
            db.session.commit()
            
            # Create notifications after successful transaction
            try:
                # Notify recipient of received money
                NotificationService.notify_transaction_received(
                    user_id=recipient_id,
                    amount=str(amount),
                    sender_name=sender.name,
                    transaction_id=transaction.id
                )
                
                # Notify sender of sent money
                NotificationService.notify_transaction_sent(
                    user_id=sender_id,
                    amount=str(amount),
                    recipient_name=recipient.name,
                    transaction_id=transaction.id
                )
            except Exception as e:
                # Log notification failure but don't fail the transaction
                AuditLog.log_system_event(
                    action_type='NOTIFICATION_FAILED',
                    entity_type='Transaction',
                    details={
                        'transaction_id': transaction.id,
                        'error': str(e)
                    }
                )
            
            return {
                'success': True,
                'transaction': transaction.to_dict(include_names=True),
                'sender_balance': sender_result['new_balance'],
                'recipient_balance': recipient_result['new_balance'],
                'warnings': sender_validation['warnings'] + recipient_validation['warnings']
            }
            
        except Exception as e:
            # Rollback on any error
            db.session.rollback()
            
            # Mark transaction as failed
            transaction.mark_as_failed()
            db.session.commit()
            
            raise ValueError(f"Transaction failed: {str(e)}")
    
    @classmethod
    def send_bulk_money(cls, sender_id: str, recipients: List[Dict[str, Any]],
                       ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Send money to multiple recipients in a single transaction
        
        Args:
            sender_id: ID of the sender
            recipients: List of recipient dictionaries with keys:
                - recipient_id: ID of recipient
                - amount: Amount to send
                - category: Optional category
                - note: Optional note
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with bulk transaction results
            
        Raises:
            ValueError: If validation fails
        """
        if not recipients:
            raise ValueError("No recipients specified")
        
        if len(recipients) > 50:  # Reasonable limit
            raise ValueError("Too many recipients (maximum 50)")
        
        # Validate sender
        sender = User.query.get(sender_id)
        if not sender or not sender.is_active():
            raise ValueError("Sender account not found or inactive")
        
        # Validate all recipients and calculate total
        total_amount = Decimal('0.00')
        validated_recipients = []
        
        for i, recipient_data in enumerate(recipients):
            try:
                recipient_id = recipient_data.get('recipient_id')
                amount = Decimal(str(recipient_data.get('amount', 0)))
                category = recipient_data.get('category')
                note = recipient_data.get('note')
                
                if not recipient_id:
                    raise ValueError(f"Recipient {i+1}: recipient_id is required")
                
                if amount <= 0:
                    raise ValueError(f"Recipient {i+1}: amount must be positive")
                
                if recipient_id == sender_id:
                    raise ValueError(f"Recipient {i+1}: cannot send money to yourself")
                
                # Validate recipient exists and is active
                recipient = User.query.get(recipient_id)
                if not recipient or not recipient.is_active():
                    raise ValueError(f"Recipient {i+1}: account not found or inactive")
                
                validated_recipients.append({
                    'recipient_id': recipient_id,
                    'recipient': recipient,
                    'amount': amount,
                    'category': category,
                    'note': note
                })
                
                total_amount += amount
                
            except (ValueError, TypeError) as e:
                raise ValueError(f"Recipient {i+1} validation failed: {str(e)}")
        
        # Validate sender can afford total amount
        sender_validation = AccountService.validate_transaction_limits(sender_id, -total_amount)
        if not sender_validation['valid']:
            error_messages = [error['message'] for error in sender_validation['errors']]
            raise ValueError(f"Sender validation failed: {'; '.join(error_messages)}")
        
        # Validate each recipient can receive their amount
        for i, recipient_data in enumerate(validated_recipients):
            recipient_validation = AccountService.validate_transaction_limits(
                recipient_data['recipient_id'], 
                recipient_data['amount']
            )
            if not recipient_validation['valid']:
                error_messages = [error['message'] for error in recipient_validation['errors']]
                raise ValueError(f"Recipient {i+1} validation failed: {'; '.join(error_messages)}")
        
        # Process all transactions atomically
        transactions = []
        results = []
        
        try:
            # Create all transaction records
            for recipient_data in validated_recipients:
                transaction = Transaction.create_transfer(
                    sender_id=sender_id,
                    recipient_id=recipient_data['recipient_id'],
                    amount=recipient_data['amount'],
                    category=recipient_data['category'],
                    note=recipient_data['note']
                )
                
                db.session.add(transaction)
                transactions.append(transaction)
            
            db.session.flush()  # Get transaction IDs
            
            # Update sender balance once with total amount
            sender_result = AccountService.update_account_balance(
                user_id=sender_id,
                amount=-total_amount,
                transaction_id=f"BULK_{transactions[0].id}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Update each recipient balance
            for i, (transaction, recipient_data) in enumerate(zip(transactions, validated_recipients)):
                recipient_result = AccountService.update_account_balance(
                    user_id=recipient_data['recipient_id'],
                    amount=recipient_data['amount'],
                    transaction_id=transaction.id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # Mark transaction as processed
                transaction.mark_as_processed()
                
                # Log transaction
                AuditLog.log_transaction(
                    transaction=transaction,
                    user_id=sender_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                results.append({
                    'transaction': transaction.to_dict(include_names=True),
                    'recipient_balance': recipient_result['new_balance']
                })
            
            # Log bulk transaction event
            AuditLog.log_user_action(
                user_id=sender_id,
                action_type='BULK_TRANSFER_COMPLETED',
                entity_type='Transaction',
                entity_id=f"BULK_{transactions[0].id}",
                new_values={
                    'total_amount': str(total_amount),
                    'recipient_count': len(recipients),
                    'transaction_ids': [t.id for t in transactions]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Commit all changes
            db.session.commit()
            
            return {
                'success': True,
                'total_amount': str(total_amount),
                'recipient_count': len(results),
                'sender_balance': sender_result['new_balance'],
                'transactions': results,
                'warnings': sender_validation['warnings']
            }
            
        except Exception as e:
            # Rollback on any error
            db.session.rollback()
            
            # Mark all transactions as failed
            for transaction in transactions:
                transaction.mark_as_failed()
            
            db.session.commit()
            
            raise ValueError(f"Bulk transaction failed: {str(e)}")
    
    @classmethod
    def validate_transaction(cls, sender_id: str, recipient_id: str = None, 
                           amount: Decimal = None, transaction_type: TransactionType = None) -> Dict[str, Any]:
        """
        Validate a transaction before processing
        
        Args:
            sender_id: ID of the sender
            recipient_id: ID of the recipient (for transfers)
            amount: Transaction amount
            transaction_type: Type of transaction
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validate sender
            sender = User.query.get(sender_id)
            if not sender or not sender.is_active():
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'INVALID_SENDER',
                    'message': 'Sender account not found or inactive'
                })
                return validation_result
            
            # Validate recipient for transfers
            if recipient_id and transaction_type == TransactionType.TRANSFER:
                if sender_id == recipient_id:
                    validation_result['valid'] = False
                    validation_result['errors'].append({
                        'code': 'SELF_TRANSFER',
                        'message': 'Cannot send money to yourself'
                    })
                    return validation_result
                
                recipient = User.query.get(recipient_id)
                if not recipient or not recipient.is_active():
                    validation_result['valid'] = False
                    validation_result['errors'].append({
                        'code': 'INVALID_RECIPIENT',
                        'message': 'Recipient account not found or inactive'
                    })
                    return validation_result
            
            # Validate amount
            if amount is not None:
                if amount <= 0:
                    validation_result['valid'] = False
                    validation_result['errors'].append({
                        'code': 'INVALID_AMOUNT',
                        'message': 'Amount must be positive'
                    })
                    return validation_result
                
                # Check sender balance limits
                sender_validation = AccountService.validate_transaction_limits(sender_id, -amount)
                if not sender_validation['valid']:
                    validation_result['valid'] = False
                    validation_result['errors'].extend(sender_validation['errors'])
                
                validation_result['warnings'].extend(sender_validation['warnings'])
                
                # Check recipient balance limits for transfers
                if recipient_id and transaction_type == TransactionType.TRANSFER:
                    recipient_validation = AccountService.validate_transaction_limits(recipient_id, amount)
                    if not recipient_validation['valid']:
                        validation_result['valid'] = False
                        validation_result['errors'].extend(recipient_validation['errors'])
                    
                    validation_result['warnings'].extend(recipient_validation['warnings'])
            
            return validation_result
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append({
                'code': 'VALIDATION_ERROR',
                'message': f'Validation failed: {str(e)}'
            })
            return validation_result
    
    @classmethod
    def get_transaction_by_id(cls, transaction_id: str, user_id: str = None) -> Optional[Transaction]:
        """
        Get transaction by ID with optional user access control
        
        Args:
            transaction_id: Transaction ID
            user_id: Optional user ID for access control
            
        Returns:
            Transaction object or None if not found/accessible
        """
        query = Transaction.query.filter_by(id=transaction_id)
        
        # If user_id provided, ensure user is involved in transaction
        if user_id:
            query = query.filter(
                or_(
                    Transaction.sender_id == user_id,
                    Transaction.recipient_id == user_id
                )
            )
        
        return query.first()
    
    @classmethod
    def get_recent_transactions(cls, user_id: str, limit: int = 10) -> List[Transaction]:
        """
        Get recent transactions for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of transactions to return
            
        Returns:
            List of recent transactions
        """
        return Transaction.query.filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            )
        ).order_by(desc(Transaction.created_at)).limit(limit).all()
    
    @classmethod
    def get_transaction_statistics(cls, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get transaction statistics for a user
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with transaction statistics
        """
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get transactions in period
        transactions = Transaction.query.filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.created_at >= start_date,
            Transaction.status == TransactionStatus.COMPLETED
        ).all()
        
        # Calculate statistics
        total_sent = sum(
            t.amount for t in transactions 
            if t.sender_id == user_id
        ) or Decimal('0.00')
        
        total_received = sum(
            t.amount for t in transactions 
            if t.recipient_id == user_id
        ) or Decimal('0.00')
        
        sent_count = len([t for t in transactions if t.sender_id == user_id])
        received_count = len([t for t in transactions if t.recipient_id == user_id])
        
        # Get most frequent transaction partners
        partners = {}
        for transaction in transactions:
            if transaction.sender_id == user_id and transaction.recipient_id:
                partner_id = transaction.recipient_id
                partner_name = transaction.recipient.name if transaction.recipient else 'Unknown'
            elif transaction.recipient_id == user_id:
                partner_id = transaction.sender_id
                partner_name = transaction.sender.name if transaction.sender else 'Unknown'
            else:
                continue
            
            if partner_id not in partners:
                partners[partner_id] = {
                    'name': partner_name,
                    'transaction_count': 0,
                    'total_amount': Decimal('0.00')
                }
            
            partners[partner_id]['transaction_count'] += 1
            partners[partner_id]['total_amount'] += transaction.amount
        
        # Sort partners by transaction count
        top_partners = sorted(
            partners.items(),
            key=lambda x: x[1]['transaction_count'],
            reverse=True
        )[:5]
        
        return {
            'period_days': days,
            'total_transactions': len(transactions),
            'total_sent': str(total_sent),
            'total_received': str(total_received),
            'net_amount': str(total_received - total_sent),
            'sent_count': sent_count,
            'received_count': received_count,
            'average_sent': str(total_sent / sent_count) if sent_count > 0 else '0.00',
            'average_received': str(total_received / received_count) if received_count > 0 else '0.00',
            'top_partners': [
                {
                    'user_id': partner_id,
                    'name': data['name'],
                    'transaction_count': data['transaction_count'],
                    'total_amount': str(data['total_amount'])
                }
                for partner_id, data in top_partners
            ]
        }
    
    @classmethod
    def cancel_transaction(cls, transaction_id: str, user_id: str,
                          ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Cancel a transaction (if possible)
        Note: In this system, transactions are processed immediately,
        so cancellation is only possible for failed transactions
        
        Args:
            transaction_id: Transaction ID to cancel
            user_id: User requesting cancellation
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with cancellation result
            
        Raises:
            ValueError: If transaction cannot be cancelled
        """
        transaction = cls.get_transaction_by_id(transaction_id, user_id)
        
        if not transaction:
            raise ValueError("Transaction not found or access denied")
        
        if transaction.status == TransactionStatus.COMPLETED:
            raise ValueError("Cannot cancel completed transaction")
        
        if transaction.status == TransactionStatus.FAILED:
            # Already failed, just log the cancellation attempt
            AuditLog.log_user_action(
                user_id=user_id,
                action_type='TRANSACTION_CANCEL_ATTEMPTED',
                entity_type='Transaction',
                entity_id=transaction_id,
                new_values={'status': 'already_failed'},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                'success': True,
                'message': 'Transaction was already failed',
                'transaction': transaction.to_dict()
            }
        
        # For any other status, mark as failed
        transaction.mark_as_failed()
        
        # Log cancellation
        AuditLog.log_user_action(
            user_id=user_id,
            action_type='TRANSACTION_CANCELLED',
            entity_type='Transaction',
            entity_id=transaction_id,
            old_values={'status': 'pending'},
            new_values={'status': 'failed'},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Transaction cancelled successfully',
            'transaction': transaction.to_dict()
        }