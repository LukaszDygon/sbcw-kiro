"""
Event service for SoftBankCashWire
Handles event account creation, contributions, and lifecycle management
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func
from models import (
    db, User, EventAccount, EventStatus, Transaction, TransactionType, 
    TransactionStatus, AuditLog, generate_uuid
)
from services.transaction_service import TransactionService
from services.notification_service import NotificationService

class EventService:
    """Service for managing event accounts and contributions"""
    
    @classmethod
    def create_event_account(cls, creator_id: str, event_data: Dict[str, Any],
                           ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Create a new event account
        
        Args:
            creator_id: ID of the user creating the event
            event_data: Dictionary containing event details:
                - name: Event name (required)
                - description: Event description (required)
                - target_amount: Optional target amount
                - deadline: Optional deadline (ISO format)
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with event creation result
            
        Raises:
            ValueError: If validation fails
        """
        # Validate creator
        creator = User.query.get(creator_id)
        if not creator or not creator.is_active():
            raise ValueError("Creator account not found or inactive")
        
        # Validate required fields
        name = event_data.get('name', '').strip()
        description = event_data.get('description', '').strip()
        
        if not name:
            raise ValueError("Event name is required")
        
        if not description:
            raise ValueError("Event description is required")
        
        if len(name) > 255:
            raise ValueError("Event name cannot exceed 255 characters")
        
        if len(description) > 1000:
            raise ValueError("Event description cannot exceed 1000 characters")
        
        # Validate optional fields
        target_amount = None
        if event_data.get('target_amount'):
            try:
                target_amount = Decimal(str(event_data['target_amount']))
                if target_amount <= 0:
                    raise ValueError("Target amount must be positive")
            except (ValueError, TypeError):
                raise ValueError("Target amount must be a valid positive number")
        
        deadline = None
        if event_data.get('deadline'):
            try:
                deadline = datetime.fromisoformat(event_data['deadline'].replace('Z', '+00:00'))
                if deadline <= datetime.utcnow():
                    raise ValueError("Deadline must be in the future")
            except (ValueError, TypeError):
                raise ValueError("Deadline must be a valid ISO format date in the future")
        
        try:
            # Create event account
            event_account = EventAccount(
                creator_id=creator_id,
                name=name,
                description=description,
                target_amount=target_amount,
                deadline=deadline,
                status=EventStatus.ACTIVE
            )
            
            db.session.add(event_account)
            db.session.flush()  # Get event ID
            
            # Log event creation
            AuditLog.log_event_action(
                event_account=event_account,
                user_id=creator_id,
                action_type='EVENT_CREATED',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.commit()
            
            return {
                'success': True,
                'event': event_account.to_dict(include_creator_name=True)
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to create event account: {str(e)}")
    
    @classmethod
    def contribute_to_event(cls, user_id: str, event_id: str, amount: Decimal,
                          note: str = None, ip_address: str = None, 
                          user_agent: str = None) -> Dict[str, Any]:
        """
        Contribute money to an event account
        
        Args:
            user_id: ID of the user making the contribution
            event_id: ID of the event account
            amount: Contribution amount
            note: Optional contribution note
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with contribution result
            
        Raises:
            ValueError: If contribution cannot be processed
        """
        # Validate user
        user = User.query.get(user_id)
        if not user or not user.is_active():
            raise ValueError("User account not found or inactive")
        
        # Validate event
        event_account = EventAccount.query.get(event_id)
        if not event_account:
            raise ValueError("Event account not found")
        
        if not event_account.can_receive_contributions():
            raise ValueError("Event account is not accepting contributions")
        
        # Check if deadline has passed
        if event_account.has_deadline_passed():
            raise ValueError("Event deadline has passed")
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Contribution amount must be positive")
        
        # Use transaction service to process the contribution
        try:
            result = TransactionService.send_money(
                sender_id=user_id,
                recipient_id=None,  # No recipient for event contributions
                amount=amount,
                category="Event Contribution",
                note=note or f"Contribution to {event_account.name}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Update the transaction to be an event contribution
            transaction = Transaction.query.get(result['transaction']['id'])
            transaction.transaction_type = TransactionType.EVENT_CONTRIBUTION
            transaction.event_id = event_id
            transaction.recipient_id = None
            
            # Log event contribution
            AuditLog.log_event_action(
                event_account=event_account,
                user_id=user_id,
                action_type='EVENT_CONTRIBUTION_MADE',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.commit()
            
            # Get updated event data
            db.session.refresh(event_account)
            
            # Create notification for event creator about the contribution
            try:
                NotificationService.notify_event_contribution(
                    user_id=event_account.creator_id,
                    event_name=event_account.name,
                    amount=str(amount),
                    contributor_name=user.name,
                    event_id=event_id
                )
            except Exception as e:
                # Log notification failure but don't fail the contribution
                AuditLog.log_system_event(
                    action_type='NOTIFICATION_FAILED',
                    entity_type='EventAccount',
                    details={
                        'event_id': event_id,
                        'contribution_transaction_id': transaction.id,
                        'error': str(e)
                    }
                )
            
            return {
                'success': True,
                'contribution': result['transaction'],
                'contributor_balance': result['sender_balance'],
                'event': event_account.to_dict(include_creator_name=True),
                'warnings': result.get('warnings', [])
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to process contribution: {str(e)}")
    
    @classmethod
    def close_event_account(cls, event_id: str, closer_id: str,
                          ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Close an event account
        
        Args:
            event_id: ID of the event account
            closer_id: ID of the user closing the event (must be creator or admin)
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with closure result
            
        Raises:
            ValueError: If event cannot be closed
        """
        # Validate user
        closer = User.query.get(closer_id)
        if not closer or not closer.is_active():
            raise ValueError("User account not found or inactive")
        
        # Validate event
        event_account = EventAccount.query.get(event_id)
        if not event_account:
            raise ValueError("Event account not found")
        
        if not event_account.is_active():
            raise ValueError("Event account is not active")
        
        # Check permissions (creator or admin can close)
        if event_account.creator_id != closer_id and not closer.can_access_admin_features():
            raise ValueError("Only the event creator or admin can close this event")
        
        try:
            # Close the event
            event_account.close_event()
            
            # Log event closure
            AuditLog.log_event_action(
                event_account=event_account,
                user_id=closer_id,
                action_type='EVENT_CLOSED',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Notify finance team (in a real system, this would send notifications)
            AuditLog.log_system_event(
                action_type='FINANCE_NOTIFICATION_REQUIRED',
                entity_type='EventAccount',
                entity_id=event_id,
                details={
                    'event_name': event_account.name,
                    'total_contributions': str(event_account.total_contributions),
                    'contributor_count': event_account.get_contributor_count(),
                    'closed_by': closer.name
                }
            )
            
            db.session.commit()
            
            # Create notifications for event closure
            try:
                # Get all contributors to notify them
                contributors = cls.get_event_contributors(event_id)
                
                # Notify all contributors about event closure
                for contributor in contributors:
                    if contributor['user_id'] != event_account.creator_id:  # Don't notify creator twice
                        NotificationService.notify_event_closed(
                            user_id=contributor['user_id'],
                            event_name=event_account.name,
                            event_id=event_id
                        )
                
                # Notify event creator if they didn't close it themselves
                if event_account.creator_id != closer_id:
                    NotificationService.notify_event_closed(
                        user_id=event_account.creator_id,
                        event_name=event_account.name,
                        event_id=event_id
                    )
                
            except Exception as e:
                # Log notification failure but don't fail the closure
                AuditLog.log_system_event(
                    action_type='NOTIFICATION_FAILED',
                    entity_type='EventAccount',
                    details={
                        'event_id': event_id,
                        'error': str(e)
                    }
                )
            
            return {
                'success': True,
                'event': event_account.to_dict(include_creator_name=True),
                'message': 'Event closed successfully. Finance team has been notified for fund disbursement.'
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to close event: {str(e)}")
    
    @classmethod
    def cancel_event_account(cls, event_id: str, canceller_id: str,
                           ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Cancel an event account
        
        Args:
            event_id: ID of the event account
            canceller_id: ID of the user cancelling the event (must be creator or admin)
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
            
        Returns:
            Dictionary with cancellation result
            
        Raises:
            ValueError: If event cannot be cancelled
        """
        # Validate user
        canceller = User.query.get(canceller_id)
        if not canceller or not canceller.is_active():
            raise ValueError("User account not found or inactive")
        
        # Validate event
        event_account = EventAccount.query.get(event_id)
        if not event_account:
            raise ValueError("Event account not found")
        
        if not event_account.is_active():
            raise ValueError("Event account is not active")
        
        # Check permissions (creator or admin can cancel)
        if event_account.creator_id != canceller_id and not canceller.can_access_admin_features():
            raise ValueError("Only the event creator or admin can cancel this event")
        
        # Check if there are contributions (might need refunds)
        if event_account.total_contributions > 0:
            raise ValueError("Cannot cancel event with existing contributions. Please close the event instead.")
        
        try:
            # Cancel the event
            event_account.cancel_event()
            
            # Log event cancellation
            AuditLog.log_event_action(
                event_account=event_account,
                user_id=canceller_id,
                action_type='EVENT_CANCELLED',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.session.commit()
            
            return {
                'success': True,
                'event': event_account.to_dict(include_creator_name=True),
                'message': 'Event cancelled successfully.'
            }
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to cancel event: {str(e)}")
    
    @classmethod
    def get_event_by_id(cls, event_id: str, include_contributions: bool = False) -> Optional[EventAccount]:
        """
        Get event account by ID
        
        Args:
            event_id: Event ID
            include_contributions: Whether to include contribution details
            
        Returns:
            EventAccount object or None if not found
        """
        event = EventAccount.query.get(event_id)
        
        if event and include_contributions:
            # Eager load contributions to avoid N+1 queries
            event.contributions
        
        return event
    
    @classmethod
    def get_active_events(cls, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get active event accounts
        
        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            Dictionary with events and pagination info
        """
        query = EventAccount.query.filter_by(status=EventStatus.ACTIVE)
        query = query.order_by(desc(EventAccount.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        events = query.limit(limit).offset(offset).all()
        
        return {
            'events': [event.to_dict(include_creator_name=True) for event in events],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(events)) < total
            }
        }
    
    @classmethod
    def get_events_by_creator(cls, creator_id: str, status: EventStatus = None,
                            limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get events created by a specific user
        
        Args:
            creator_id: Creator user ID
            status: Optional status filter
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            Dictionary with events and pagination info
        """
        query = EventAccount.query.filter_by(creator_id=creator_id)
        
        if status:
            query = query.filter_by(status=status)
        
        query = query.order_by(desc(EventAccount.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        events = query.limit(limit).offset(offset).all()
        
        return {
            'events': [event.to_dict(include_creator_name=True) for event in events],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(events)) < total
            }
        }
    
    @classmethod
    def get_user_contributions(cls, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get contributions made by a user to events
        
        Args:
            user_id: User ID
            limit: Maximum number of contributions to return
            offset: Number of contributions to skip
            
        Returns:
            Dictionary with contributions and pagination info
        """
        query = Transaction.query.filter(
            Transaction.sender_id == user_id,
            Transaction.transaction_type == TransactionType.EVENT_CONTRIBUTION,
            Transaction.status == TransactionStatus.COMPLETED
        ).order_by(desc(Transaction.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        contributions = query.limit(limit).offset(offset).all()
        
        return {
            'contributions': [contrib.to_dict(include_names=True) for contrib in contributions],
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(contributions)) < total
            }
        }
    
    @classmethod
    def get_event_contributions(cls, event_id: str) -> List[Dict[str, Any]]:
        """
        Get all contributions for a specific event
        
        Args:
            event_id: Event ID
            
        Returns:
            List of contribution details
        """
        contributions = Transaction.query.filter(
            Transaction.event_id == event_id,
            Transaction.transaction_type == TransactionType.EVENT_CONTRIBUTION,
            Transaction.status == TransactionStatus.COMPLETED
        ).order_by(desc(Transaction.created_at)).all()
        
        return [
            {
                'id': contrib.id,
                'contributor_id': contrib.sender_id,
                'contributor_name': contrib.sender.name if contrib.sender else 'Unknown',
                'amount': str(contrib.amount),
                'note': contrib.note,
                'created_at': contrib.created_at.isoformat() if contrib.created_at else None
            }
            for contrib in contributions
        ]
    
    @classmethod
    def get_events_expiring_soon(cls, hours: int = 24) -> List[EventAccount]:
        """
        Get events with deadlines expiring soon
        
        Args:
            hours: Hours until deadline to consider "expiring soon"
            
        Returns:
            List of expiring events
        """
        deadline_threshold = datetime.utcnow() + timedelta(hours=hours)
        
        return EventAccount.query.filter(
            EventAccount.status == EventStatus.ACTIVE,
            EventAccount.deadline.isnot(None),
            EventAccount.deadline <= deadline_threshold,
            EventAccount.deadline > datetime.utcnow()
        ).all()
    
    @classmethod
    def get_event_statistics(cls, days: int = 30) -> Dict[str, Any]:
        """
        Get event statistics for a time period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with event statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get events created in period
        events_created = EventAccount.query.filter(
            EventAccount.created_at >= start_date
        ).count()
        
        # Get events by status
        active_events = EventAccount.query.filter(
            EventAccount.status == EventStatus.ACTIVE
        ).count()
        
        closed_events = EventAccount.query.filter(
            EventAccount.status == EventStatus.CLOSED,
            EventAccount.closed_at >= start_date
        ).count()
        
        cancelled_events = EventAccount.query.filter(
            EventAccount.status == EventStatus.CANCELLED,
            EventAccount.closed_at >= start_date
        ).count()
        
        # Get contribution statistics
        contributions = Transaction.query.filter(
            Transaction.transaction_type == TransactionType.EVENT_CONTRIBUTION,
            Transaction.status == TransactionStatus.COMPLETED,
            Transaction.created_at >= start_date
        ).all()
        
        total_contributions = len(contributions)
        total_amount = sum(contrib.amount for contrib in contributions) or Decimal('0.00')
        average_contribution = (total_amount / total_contributions) if total_contributions > 0 else Decimal('0.00')
        
        # Get unique contributors
        unique_contributors = len(set(contrib.sender_id for contrib in contributions))
        
        # Get most popular events (by contribution count)
        event_contribution_counts = {}
        for contrib in contributions:
            if contrib.event_id:
                event_contribution_counts[contrib.event_id] = event_contribution_counts.get(contrib.event_id, 0) + 1
        
        popular_events = sorted(
            event_contribution_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        popular_events_data = []
        for event_id, contrib_count in popular_events:
            event = EventAccount.query.get(event_id)
            if event:
                popular_events_data.append({
                    'event_id': event_id,
                    'event_name': event.name,
                    'contribution_count': contrib_count,
                    'total_contributions': str(event.total_contributions)
                })
        
        return {
            'period_days': days,
            'events_created': events_created,
            'active_events': active_events,
            'closed_events': closed_events,
            'cancelled_events': cancelled_events,
            'contributions': {
                'total_count': total_contributions,
                'total_amount': str(total_amount),
                'average_amount': str(average_contribution),
                'unique_contributors': unique_contributors
            },
            'popular_events': popular_events_data
        }
    
    @classmethod
    def search_events(cls, search_term: str, status: EventStatus = None,
                     limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Search events by name or description
        
        Args:
            search_term: Search term
            status: Optional status filter
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            Dictionary with matching events and pagination info
        """
        query = EventAccount.query.filter(
            or_(
                EventAccount.name.ilike(f"%{search_term}%"),
                EventAccount.description.ilike(f"%{search_term}%")
            )
        )
        
        if status:
            query = query.filter_by(status=status)
        
        query = query.order_by(desc(EventAccount.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        events = query.limit(limit).offset(offset).all()
        
        return {
            'events': [event.to_dict(include_creator_name=True) for event in events],
            'search_term': search_term,
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(events)) < total
            }
        }
    
    @classmethod
    def validate_event_creation(cls, creator_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate event creation without creating it
        
        Args:
            creator_id: Creator user ID
            event_data: Event data to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validate creator
            creator = User.query.get(creator_id)
            if not creator or not creator.is_active():
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'INVALID_CREATOR',
                    'message': 'Creator account not found or inactive'
                })
                return validation_result
            
            # Validate required fields
            name = event_data.get('name', '').strip()
            description = event_data.get('description', '').strip()
            
            if not name:
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'MISSING_NAME',
                    'message': 'Event name is required'
                })
            elif len(name) > 255:
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'NAME_TOO_LONG',
                    'message': 'Event name cannot exceed 255 characters'
                })
            
            if not description:
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'MISSING_DESCRIPTION',
                    'message': 'Event description is required'
                })
            elif len(description) > 1000:
                validation_result['valid'] = False
                validation_result['errors'].append({
                    'code': 'DESCRIPTION_TOO_LONG',
                    'message': 'Event description cannot exceed 1000 characters'
                })
            
            # Validate optional fields
            if event_data.get('target_amount'):
                try:
                    target_amount = Decimal(str(event_data['target_amount']))
                    if target_amount <= 0:
                        validation_result['valid'] = False
                        validation_result['errors'].append({
                            'code': 'INVALID_TARGET_AMOUNT',
                            'message': 'Target amount must be positive'
                        })
                except (ValueError, TypeError):
                    validation_result['valid'] = False
                    validation_result['errors'].append({
                        'code': 'INVALID_TARGET_AMOUNT',
                        'message': 'Target amount must be a valid positive number'
                    })
            
            if event_data.get('deadline'):
                try:
                    deadline = datetime.fromisoformat(event_data['deadline'].replace('Z', '+00:00'))
                    if deadline <= datetime.utcnow():
                        validation_result['valid'] = False
                        validation_result['errors'].append({
                            'code': 'INVALID_DEADLINE',
                            'message': 'Deadline must be in the future'
                        })
                except (ValueError, TypeError):
                    validation_result['valid'] = False
                    validation_result['errors'].append({
                        'code': 'INVALID_DEADLINE',
                        'message': 'Deadline must be a valid ISO format date'
                    })
            
            return validation_result
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append({
                'code': 'VALIDATION_ERROR',
                'message': f'Validation failed: {str(e)}'
            })
            return validation_result