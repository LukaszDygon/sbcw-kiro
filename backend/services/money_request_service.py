"""
Money request service for SoftBankCashWire
Handles payment requests between users with approval/decline workflow
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc
from models import (
    db, User, MoneyRequest, RequestStatus, Transaction, TransactionType,
    AuditLog, generate_uuid
)
from services.transaction_service import TransactionService
from services.notification_service import NotificationService

class MoneyRequestService:
    """Service for managing money requests between users"""
    
    DEFAULT_EXPIRY_DAYS = 7
    MAX_EXPIRY_DAYS = 30
    
    @classmethod
    def create_money_request(cls, requester_id: str, recipient_id: str, amount: Decimal,
                           note: str = None, expires_in_days: int = None,
                           ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Create a new money request
        
        Args:
            requester_id: ID of the user requesting money
            recipient_id: ID of the user being asked for money
            amount: Amount being requested
            note: Optional note explaining the request
            expires_in_days: Days until request expires (default: 7, max: 30)
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with request creation result
            
        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        if requester_id == recipient_id:
            raise ValueError("Cannot request money from yourself")
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if expires_in_days is None:
            expires_in_days = cls.DEFAULT_EXPIRY_DAYS
        elif expires_in_days < 1 or expires_in_days > cls.MAX_EXPIRY_DAYS:
            raise ValueError(f"Expiry days must be between 1 and {cls.MAX_EXPIRY_DAYS}")
        
        # Validate users exist and are active
        requester = User.query.get(requester_id)
        recipient = User.query.get(recipient_id)
        
        if not requester or not requester.is_active():
            raise ValueError("Requester account not found or inactive")
        
        if not recipient or not recipient.is_active():
            raise ValueError("Recipient account not found or inactive")
        
        # Check for duplicate pending requests
        existing_request = MoneyRequest.query.filter(
            MoneyRequest.requester_id == requester_id,
            MoneyRequest.recipient_id == recipient_id,
            MoneyRequest.status == RequestStatus.PENDING,
            MoneyRequest.expires_at > datetime.now(datetime.UTC)
        ).first()
        
        if existing_request:
            raise ValueError("You already have a pending request to this user")
        
        try:
            # Create money request
            money_request = MoneyRequest.create_request(
                requester_id=requester_id,
                recipient_id=recipient_id,
                amount=amount,
                note=note,
                expires_in_days=expires_in_days
            )
            
            db.session.add(money_request)
            db.session.flush()  # Get request ID
            
            # Log request creation
            AuditLog.log_money_request_action(
                money_request=money_request,
                user_id=requester_id,
                action_type='MONEY_REQUEST_CREATED',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.commit()
            
            # Create notification for recipient after successful creation
            try:
                NotificationService.notify_money_request_received(
                    user_id=recipient_id,
                    amount=str(amount),
                    requester_name=requester.name,
                    request_id=money_request.id
                )
            except Exception as e:
                # Log notification failure but don't fail the request creation
                AuditLog.log_system_event(
                    action_type='NOTIFICATION_FAILED',
                    entity_type='MoneyRequest',
                    details={
                        'money_request_id': money_request.id,
                        'error': str(e)
                    }
                )
            
            return {
                'success': True,
                'request': money_request.to_dict(include_names=True),
                'expires_in_hours': int((money_request.expires_at - datetime.now(datetime.UTC)).total_seconds() / 3600)
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to create money request: {str(e)}")
    
    @classmethod
    def respond_to_request(cls, request_id: str, user_id: str, approved: bool,
                          ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Respond to a money request (approve or decline)
        
        Args:
            request_id: ID of the money request
            user_id: ID of the user responding (must be recipient)
            approved: True to approve, False to decline
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with response result
            
        Raises:
            ValueError: If request cannot be processed
        """
        # Get money request
        money_request = MoneyRequest.query.get(request_id)
        
        if not money_request:
            raise ValueError("Money request not found")
        
        # Validate user is the recipient
        if money_request.recipient_id != user_id:
            raise ValueError("You are not authorized to respond to this request")
        
        # Check if request can be responded to
        if not money_request.can_be_responded_to():
            if money_request.is_expired():
                raise ValueError("This request has expired")
            else:
                raise ValueError("This request has already been responded to")
        
        try:
            # Fetch recipient user for notification context
            recipient = User.query.get(money_request.recipient_id)
            if approved:
                # Approve the request
                money_request.approve()
                
                # Process the actual money transfer
                transfer_result = TransactionService.send_money(
                    sender_id=money_request.recipient_id,  # Recipient becomes sender
                    recipient_id=money_request.requester_id,  # Requester becomes recipient
                    amount=money_request.amount,
                    category="Money Request",
                    note=f"Payment for request: {money_request.note or 'No description'}",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                # Log approval and transfer
                AuditLog.log_money_request_action(
                    money_request=money_request,
                    user_id=user_id,
                    action_type='MONEY_REQUEST_APPROVED',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                db.session.commit()
                
                # Create notification for requester after successful approval
                try:
                    NotificationService.notify_money_request_approved(
                        user_id=money_request.requester_id,
                        amount=str(money_request.amount),
                        approver_name=recipient.name,
                        request_id=money_request.id
                    )
                except Exception as e:
                    # Log notification failure but don't fail the approval
                    AuditLog.log_system_event(
                        action_type='NOTIFICATION_FAILED',
                        entity_type='MoneyRequest',
                        details={
                            'money_request_id': money_request.id,
                            'error': str(e)
                        }
                    )
                
                return {
                    'success': True,
                    'approved': True,
                    'request': money_request.to_dict(include_names=True),
                    'transaction': transfer_result['transaction'],
                    'sender_balance': transfer_result['sender_balance'],
                    'recipient_balance': transfer_result['recipient_balance']
                }
                
            else:
                # Decline the request
                money_request.decline()
                
                # Log decline
                AuditLog.log_money_request_action(
                    money_request=money_request,
                    user_id=user_id,
                    action_type='MONEY_REQUEST_DECLINED',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                db.session.commit()
                
                # Create notification for requester after decline
                try:
                    NotificationService.notify_money_request_declined(
                        user_id=money_request.requester_id,
                        amount=str(money_request.amount),
                        decliner_name=recipient.name,
                        request_id=money_request.id
                    )
                except Exception as e:
                    # Log notification failure but don't fail the decline
                    AuditLog.log_system_event(
                        action_type='NOTIFICATION_FAILED',
                        entity_type='MoneyRequest',
                        details={
                            'money_request_id': money_request.id,
                            'error': str(e)
                        }
                    )
                
                return {
                    'success': True,
                    'approved': False,
                    'request': money_request.to_dict(include_names=True),
                    'message': 'Request declined successfully'
                }
                
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to respond to request: {str(e)}")
    
    @classmethod
    def cancel_request(cls, request_id: str, user_id: str,
                      ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Cancel a money request (only by requester)
        
        Args:
            request_id: ID of the money request
            user_id: ID of the user cancelling (must be requester)
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with cancellation result
            
        Raises:
            ValueError: If request cannot be cancelled
        """
        # Get money request
        money_request = MoneyRequest.query.get(request_id)
        
        if not money_request:
            raise ValueError("Money request not found")
        
        # Validate user is the requester
        if money_request.requester_id != user_id:
            raise ValueError("You are not authorized to cancel this request")
        
        # Check if request can be cancelled
        if not money_request.is_pending():
            raise ValueError("Only pending requests can be cancelled")
        
        try:
            # Mark as declined (cancelled by requester)
            money_request.decline()
            
            # Log cancellation
            AuditLog.log_money_request_action(
                money_request=money_request,
                user_id=user_id,
                action_type='MONEY_REQUEST_CANCELLED',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.commit()
            
            return {
                'success': True,
                'request': money_request.to_dict(include_names=True),
                'message': 'Request cancelled successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to cancel request: {str(e)}")
    
    @classmethod
    def get_request_by_id(cls, request_id: str, user_id: str = None) -> Optional[MoneyRequest]:
        """
        Get money request by ID with optional user access control
        
        Args:
            request_id: Request ID
            user_id: Optional user ID for access control
            
        Returns:
            MoneyRequest object or None if not found/accessible
        """
        query = MoneyRequest.query.filter_by(id=request_id)
        
        # If user_id provided, ensure user is involved in request
        if user_id:
            query = query.filter(
                or_(
                    MoneyRequest.requester_id == user_id,
                    MoneyRequest.recipient_id == user_id
                )
            )
        
        return query.first()
    
    @classmethod
    def get_pending_requests_for_user(cls, user_id: str) -> List[MoneyRequest]:
        """
        Get all pending money requests for a user (as recipient)
        
        Args:
            user_id: User ID
            
        Returns:
            List of pending money requests
        """
        return MoneyRequest.get_pending_requests_for_user(user_id)
    
    @classmethod
    def get_sent_requests(cls, user_id: str, status: RequestStatus = None,
                         limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get money requests sent by a user
        
        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of requests to return
            offset: Number of requests to skip
            
        Returns:
            Dictionary with requests and pagination info
        """
        query = MoneyRequest.query.filter_by(requester_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by most recent first
        query = query.order_by(desc(MoneyRequest.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        requests = query.limit(limit).offset(offset).all()
        
        return {
            'requests': [req.to_dict(include_names=True) for req in requests],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(requests)) < total
            }
        }
    
    @classmethod
    def get_received_requests(cls, user_id: str, status: RequestStatus = None,
                            limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get money requests received by a user
        
        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of requests to return
            offset: Number of requests to skip
            
        Returns:
            Dictionary with requests and pagination info
        """
        query = MoneyRequest.query.filter_by(recipient_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by most recent first
        query = query.order_by(desc(MoneyRequest.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        requests = query.limit(limit).offset(offset).all()
        
        return {
            'requests': [req.to_dict(include_names=True) for req in requests],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(requests)) < total
            }
        }
    
    @classmethod
    def get_request_statistics(cls, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get money request statistics for a user
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with request statistics
        """
        start_date = datetime.now(datetime.UTC) - timedelta(days=days)
        
        # Get requests in period
        sent_requests = MoneyRequest.query.filter(
            MoneyRequest.requester_id == user_id,
            MoneyRequest.created_at >= start_date
        ).all()
        
        received_requests = MoneyRequest.query.filter(
            MoneyRequest.recipient_id == user_id,
            MoneyRequest.created_at >= start_date
        ).all()
        
        # Calculate sent statistics
        sent_total = len(sent_requests)
        sent_approved = len([r for r in sent_requests if r.is_approved()])
        sent_declined = len([r for r in sent_requests if r.is_declined()])
        sent_pending = len([r for r in sent_requests if r.is_pending()])
        sent_expired = len([r for r in sent_requests if r.is_expired()])
        
        sent_amount_approved = sum(
            r.amount for r in sent_requests if r.is_approved()
        ) or Decimal('0.00')
        
        # Calculate received statistics
        received_total = len(received_requests)
        received_approved = len([r for r in received_requests if r.is_approved()])
        received_declined = len([r for r in received_requests if r.is_declined()])
        received_pending = len([r for r in received_requests if r.is_pending()])
        received_expired = len([r for r in received_requests if r.is_expired()])
        
        received_amount_approved = sum(
            r.amount for r in received_requests if r.is_approved()
        ) or Decimal('0.00')
        
        # Calculate approval rates
        sent_approval_rate = (sent_approved / sent_total * 100) if sent_total > 0 else 0
        received_approval_rate = (received_approved / received_total * 100) if received_total > 0 else 0
        
        return {
            'period_days': days,
            'sent_requests': {
                'total': sent_total,
                'approved': sent_approved,
                'declined': sent_declined,
                'pending': sent_pending,
                'expired': sent_expired,
                'approval_rate': round(sent_approval_rate, 1),
                'total_amount_approved': str(sent_amount_approved)
            },
            'received_requests': {
                'total': received_total,
                'approved': received_approved,
                'declined': received_declined,
                'pending': received_pending,
                'expired': received_expired,
                'approval_rate': round(received_approval_rate, 1),
                'total_amount_approved': str(received_amount_approved)
            }
        }
    
    @classmethod
    def expire_old_requests(cls) -> Dict[str, Any]:
        """
        Mark expired requests as expired (background job)
        
        Returns:
            Dictionary with expiration results
        """
        expired_requests = MoneyRequest.get_expired_requests()
        
        expired_count = 0
        
        try:
            for request in expired_requests:
                request.expire()
                
                # Log expiration
                AuditLog.log_money_request_action(
                    money_request=request,
                    user_id=None,  # System action
                    action_type='MONEY_REQUEST_EXPIRED'
                )
                
                expired_count += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'expired_count': expired_count,
                'message': f'Expired {expired_count} old requests'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'expired_count': 0,
                'error': f'Failed to expire requests: {str(e)}'
            }
    
    @classmethod
    def get_expiring_requests(cls, hours: int = 24) -> List[MoneyRequest]:
        """
        Get requests that are expiring soon
        
        Args:
            hours: Hours until expiration to consider "expiring soon"
            
        Returns:
            List of expiring requests
        """
        expiry_threshold = datetime.now(datetime.UTC) + timedelta(hours=hours)
        
        return MoneyRequest.query.filter(
            MoneyRequest.status == RequestStatus.PENDING,
            MoneyRequest.expires_at <= expiry_threshold,
            MoneyRequest.expires_at > datetime.now(datetime.UTC)
        ).all()
    
    @classmethod
    def validate_request_creation(cls, requester_id: str, recipient_id: str, 
                                amount: Decimal) -> Dict[str, Any]:
        """
        Validate money request creation without creating it
        
        Args:
            requester_id: ID of the requester
            recipient_id: ID of the recipient
            amount: Requested amount
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Basic validation
            if requester_id == recipient_id:
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'SELF_REQUEST',
                    'message': 'Cannot request money from yourself'
                })
                return validation_result
            
            if amount <= 0:
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'INVALID_AMOUNT',
                    'message': 'Amount must be positive'
                })
                return validation_result
            
            # Validate users
            requester = User.query.get(requester_id)
            recipient = User.query.get(recipient_id)
            
            if not requester or not requester.is_active():
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'INVALID_REQUESTER',
                    'message': 'Requester account not found or inactive'
                })
                return validation_result
            
            if not recipient or not recipient.is_active():
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'INVALID_RECIPIENT',
                    'message': 'Recipient account not found or inactive'
                })
                return validation_result
            
            # Check for existing pending request
            existing_request = MoneyRequest.query.filter(
                MoneyRequest.requester_id == requester_id,
                MoneyRequest.recipient_id == recipient_id,
                MoneyRequest.status == RequestStatus.PENDING,
                MoneyRequest.expires_at > datetime.now(datetime.UTC)
            ).first()
            
            if existing_request:
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'DUPLICATE_REQUEST',
                    'message': 'You already have a pending request to this user'
                })
                return validation_result
            
            # Check if recipient would be able to pay (has sufficient balance)
            from services.account_service import AccountService
            try:
                recipient_validation = AccountService.validate_transaction_limits(recipient_id, -amount)
                if not recipient_validation['valid']:
                    validation_result['warnings'].append({
                        'code': 'RECIPIENT_INSUFFICIENT_FUNDS',
                        'message': 'Recipient may not have sufficient funds to fulfill this request'
                    })
            except:
                # Don't fail validation if we can't check recipient balance
                pass
            
            return validation_result
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append({
                'code': 'VALIDATION_ERROR',
                'message': f'Validation failed: {str(e)}'
            })
            return validation_result