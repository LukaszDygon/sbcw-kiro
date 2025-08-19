"""
Audit service for SoftBankCashWire
Handles comprehensive audit logging, compliance reporting, and data retention
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func, text
from models import (
    db, User, AuditLog, Transaction, EventAccount, MoneyRequest,
    Account, UserRole
)
from cryptography.fernet import Fernet
import json
import hashlib
import base64

class AuditService:
    """Service for managing audit logs and compliance reporting"""
    
    # Audit action types
    ACTION_TYPES = {
        'USER_ACTIONS': [
            'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 'USER_CREATED', 
            'USER_INFO_UPDATED', 'PASSWORD_CHANGED'
        ],
        'TRANSACTION_ACTIONS': [
            'TRANSACTION_CREATED', 'TRANSACTION_COMPLETED', 'TRANSACTION_FAILED',
            'BULK_TRANSFER_COMPLETED', 'TRANSACTION_CANCELLED'
        ],
        'ACCOUNT_ACTIONS': [
            'ACCOUNT_BALANCE_CHANGED', 'BALANCE_UPDATED_BY_TRANSACTION',
            'ACCOUNT_CREATED', 'ACCOUNT_STATUS_CHANGED'
        ],
        'EVENT_ACTIONS': [
            'EVENT_CREATED', 'EVENT_CONTRIBUTION_MADE', 'EVENT_CLOSED',
            'EVENT_CANCELLED'
        ],
        'MONEY_REQUEST_ACTIONS': [
            'MONEY_REQUEST_CREATED', 'MONEY_REQUEST_APPROVED', 
            'MONEY_REQUEST_DECLINED', 'MONEY_REQUEST_CANCELLED',
            'MONEY_REQUEST_EXPIRED'
        ],
        'SYSTEM_ACTIONS': [
            'SYSTEM_STARTUP', 'SYSTEM_SHUTDOWN', 'SYSTEM_ERROR',
            'FINANCE_NOTIFICATION_REQUIRED', 'DATA_RETENTION_CLEANUP',
            'SECURITY_ALERT'
        ]
    }
    
    @classmethod
    def log_transaction(cls, transaction, user_id: str = None, 
                       ip_address: str = None, user_agent: str = None) -> AuditLog:
        """
        Log a transaction event with comprehensive details
        
        Args:
            transaction: Transaction object
            user_id: User ID performing the action
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            AuditLog entry
        """
        transaction_data = {
            'id': transaction.id,
            'sender_id': transaction.sender_id,
            'recipient_id': transaction.recipient_id,
            'event_id': transaction.event_id,
            'amount': str(transaction.amount),
            'transaction_type': transaction.transaction_type.value,
            'category': transaction.category,
            'note': transaction.note,
            'status': transaction.status.value,
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
            'processed_at': transaction.processed_at.isoformat() if transaction.processed_at else None
        }
        
        # Add participant names for better audit trail
        if transaction.sender:
            transaction_data['sender_name'] = transaction.sender.name
        if transaction.recipient:
            transaction_data['recipient_name'] = transaction.recipient.name
        if transaction.event_account:
            transaction_data['event_name'] = transaction.event_account.name
        
        return AuditLog.log_user_action(
            user_id=user_id or transaction.sender_id,
            action_type='TRANSACTION_CREATED',
            entity_type='Transaction',
            entity_id=transaction.id,
            new_values=transaction_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_user_action(cls, user_id: str, action_type: str, entity_type: str,
                       entity_id: str = None, old_values: Dict = None,
                       new_values: Dict = None, ip_address: str = None,
                       user_agent: str = None, additional_context: Dict = None) -> AuditLog:
        """
        Log a user action with enhanced context
        
        Args:
            user_id: User performing the action
            action_type: Type of action performed
            entity_type: Type of entity affected
            entity_id: ID of the entity affected
            old_values: Previous values (for updates)
            new_values: New values
            ip_address: Client IP address
            user_agent: Client user agent
            additional_context: Additional context information
            
        Returns:
            AuditLog entry
        """
        # Enhance new_values with additional context
        enhanced_new_values = new_values.copy() if new_values else {}
        
        if additional_context:
            enhanced_new_values.update(additional_context)
        
        # Add timestamp
        enhanced_new_values['audit_timestamp'] = datetime.now(datetime.UTC).isoformat()
        
        # Add user context
        user = User.query.get(user_id)
        if user:
            enhanced_new_values['user_name'] = user.name
            enhanced_new_values['user_role'] = user.role.value
            enhanced_new_values['user_email'] = user.email
        
        return AuditLog.log_user_action(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=enhanced_new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_system_event(cls, action_type: str, entity_type: str = 'System',
                        entity_id: str = None, details: Dict = None,
                        severity: str = 'INFO') -> AuditLog:
        """
        Log a system event
        
        Args:
            action_type: Type of system action
            entity_type: Type of entity (default: System)
            entity_id: Optional entity ID
            details: Event details
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            AuditLog entry
        """
        enhanced_details = details.copy() if details else {}
        enhanced_details.update({
            'severity': severity,
            'system_timestamp': datetime.now(datetime.UTC).isoformat(),
            'event_source': 'SoftBankCashWire'
        })
        
        return AuditLog.log_system_event(
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=enhanced_details
        )
    
    @classmethod
    def log_security_event(cls, event_type: str, user_id: str = None,
                          ip_address: str = None, user_agent: str = None,
                          details: Dict = None, severity: str = 'WARNING') -> AuditLog:
        """
        Log a security-related event
        
        Args:
            event_type: Type of security event
            user_id: User involved (if any)
            ip_address: Source IP address
            user_agent: User agent string
            details: Additional security details
            severity: Event severity
            
        Returns:
            AuditLog entry
        """
        security_details = details.copy() if details else {}
        security_details.update({
            'event_category': 'SECURITY',
            'severity': severity,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.now(datetime.UTC).isoformat()
        })
        
        if user_id:
            user = User.query.get(user_id)
            if user:
                security_details['user_name'] = user.name
                security_details['user_email'] = user.email
        
        return AuditLog.log_user_action(
            user_id=user_id,
            action_type=f'SECURITY_{event_type}',
            entity_type='Security',
            new_values=security_details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def get_audit_logs(cls, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get audit logs with filtering and pagination
        
        Args:
            filters: Dictionary of filters:
                - user_id: Filter by user
                - action_type: Filter by action type
                - entity_type: Filter by entity type
                - start_date: Start date for filtering
                - end_date: End date for filtering
                - ip_address: Filter by IP address
                - severity: Filter by severity (for system events)
                - page: Page number (default: 1)
                - per_page: Items per page (default: 50, max: 1000)
                - include_system_events: Include system events (default: True)
                
        Returns:
            Dictionary with audit logs and pagination info
        """
        if filters is None:
            filters = {}
        
        # Base query
        query = AuditLog.query
        
        # Apply filters
        if filters.get('user_id'):
            query = query.filter(AuditLog.user_id == filters['user_id'])
        
        if filters.get('action_type'):
            query = query.filter(AuditLog.action_type == filters['action_type'])
        
        if filters.get('entity_type'):
            query = query.filter(AuditLog.entity_type == filters['entity_type'])
        
        if filters.get('start_date'):
            query = query.filter(AuditLog.created_at >= filters['start_date'])
        
        if filters.get('end_date'):
            query = query.filter(AuditLog.created_at <= filters['end_date'])
        
        if filters.get('ip_address'):
            query = query.filter(AuditLog.ip_address == filters['ip_address'])
        
        # Filter by severity (stored in new_values JSON)
        if filters.get('severity'):
            query = query.filter(
                AuditLog.new_values.op('->>')('severity') == filters['severity']
            )
        
        # Exclude system events if requested
        if not filters.get('include_system_events', True):
            query = query.filter(AuditLog.user_id.isnot(None))
        
        # Order by most recent first
        query = query.order_by(desc(AuditLog.created_at))
        
        # Apply pagination
        page = filters.get('page', 1)
        per_page = min(filters.get('per_page', 50), 1000)
        
        paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Format audit logs
        audit_logs = []
        for log in paginated.items:
            log_dict = log.to_dict(include_user_name=True)
            
            # Add computed fields
            log_dict['is_system_event'] = log.user_id is None
            log_dict['severity'] = log.new_values.get('severity', 'INFO') if log.new_values else 'INFO'
            
            # Parse changes if available
            changes = log.get_changes()
            if changes:
                log_dict['changes'] = changes
            
            audit_logs.append(log_dict)
        
        return {
            'audit_logs': audit_logs,
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
    def get_user_audit_logs(cls, user_id: str, start_date: datetime = None, 
                           end_date: datetime = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get audit logs for a specific user
        
        Args:
            user_id: User ID to filter by
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of logs to return
            
        Returns:
            Dictionary with audit logs and metadata
        """
        try:
            query = AuditLog.query.filter(AuditLog.user_id == user_id)
            
            # Apply date filters
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            # Order by most recent first and limit
            logs = query.order_by(desc(AuditLog.created_at)).limit(limit).all()
            
            # Format logs
            formatted_logs = []
            for log in logs:
                log_data = {
                    'id': log.id,
                    'action_type': log.action_type,
                    'entity_type': log.entity_type,
                    'entity_id': log.entity_id,
                    'created_at': log.created_at.isoformat(),
                    'severity': getattr(log, 'severity', 'INFO'),
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent
                }
                
                # Add decrypted values if available
                if log.old_values:
                    try:
                        log_data['old_values'] = cls._decrypt_audit_data(log.old_values)
                    except:
                        log_data['old_values'] = 'Encrypted'
                
                if log.new_values:
                    try:
                        log_data['new_values'] = cls._decrypt_audit_data(log.new_values)
                    except:
                        log_data['new_values'] = 'Encrypted'
                
                formatted_logs.append(log_data)
            
            return {
                'audit_logs': formatted_logs,
                'total_count': len(formatted_logs),
                'user_id': user_id,
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            cls.log_system_event(
                'AUDIT_USER_LOGS_ERROR',
                {'error': str(e), 'user_id': user_id}
            )
            return {
                'audit_logs': [],
                'total_count': 0,
                'error': str(e)
            }
    
    @classmethod
    def generate_audit_report(cls, start_date: datetime, end_date: datetime,
                            report_type: str = 'COMPREHENSIVE') -> Dict[str, Any]:
        """
        Generate comprehensive audit report for compliance
        
        Args:
            start_date: Report start date
            end_date: Report end date
            report_type: Type of report (COMPREHENSIVE, TRANSACTIONS, SECURITY, USER_ACTIVITY)
            
        Returns:
            Dictionary with audit report data
        """
        report_data = {
            'report_type': report_type,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'generated_at': datetime.now(datetime.UTC).isoformat(),
            'generated_by': 'AuditService'
        }
        
        # Base query for the period
        base_query = AuditLog.query.filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        )
        
        if report_type in ['COMPREHENSIVE', 'USER_ACTIVITY']:
            # User activity statistics
            user_activity = cls._generate_user_activity_report(base_query)
            report_data['user_activity'] = user_activity
        
        if report_type in ['COMPREHENSIVE', 'TRANSACTIONS']:
            # Transaction statistics
            transaction_stats = cls._generate_transaction_report(base_query)
            report_data['transactions'] = transaction_stats
        
        if report_type in ['COMPREHENSIVE', 'SECURITY']:
            # Security events
            security_events = cls._generate_security_report(base_query)
            report_data['security'] = security_events
        
        if report_type == 'COMPREHENSIVE':
            # System health and events
            system_events = cls._generate_system_report(base_query)
            report_data['system'] = system_events
            
            # Compliance summary
            compliance_summary = cls._generate_compliance_summary(base_query)
            report_data['compliance'] = compliance_summary
        
        return report_data
    
    @classmethod
    def _generate_user_activity_report(cls, base_query) -> Dict[str, Any]:
        """Generate user activity section of audit report"""
        # Total user actions
        user_actions = base_query.filter(AuditLog.user_id.isnot(None)).all()
        
        # Group by user
        user_stats = {}
        for log in user_actions:
            user_id = log.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'user_name': log.user.name if log.user else 'Unknown',
                    'user_email': log.user.email if log.user else 'Unknown',
                    'total_actions': 0,
                    'action_types': {},
                    'login_count': 0,
                    'transaction_count': 0,
                    'last_activity': None
                }
            
            user_stats[user_id]['total_actions'] += 1
            
            # Count by action type
            action_type = log.action_type
            user_stats[user_id]['action_types'][action_type] = \
                user_stats[user_id]['action_types'].get(action_type, 0) + 1
            
            # Special counters
            if 'LOGIN' in action_type:
                user_stats[user_id]['login_count'] += 1
            if 'TRANSACTION' in action_type:
                user_stats[user_id]['transaction_count'] += 1
            
            # Update last activity
            if (user_stats[user_id]['last_activity'] is None or 
                log.created_at > user_stats[user_id]['last_activity']):
                user_stats[user_id]['last_activity'] = log.created_at.isoformat()
        
        return {
            'total_users_active': len(user_stats),
            'total_user_actions': len(user_actions),
            'user_details': user_stats
        }
    
    @classmethod
    def _generate_transaction_report(cls, base_query) -> Dict[str, Any]:
        """Generate transaction section of audit report"""
        transaction_logs = base_query.filter(
            AuditLog.action_type.like('%TRANSACTION%')
        ).all()
        
        transaction_stats = {
            'total_transaction_events': len(transaction_logs),
            'transaction_types': {},
            'failed_transactions': 0,
            'bulk_transfers': 0,
            'total_amount_processed': 0
        }
        
        for log in transaction_logs:
            action_type = log.action_type
            transaction_stats['transaction_types'][action_type] = \
                transaction_stats['transaction_types'].get(action_type, 0) + 1
            
            if 'FAILED' in action_type:
                transaction_stats['failed_transactions'] += 1
            
            if 'BULK' in action_type:
                transaction_stats['bulk_transfers'] += 1
            
            # Extract amount if available
            if log.new_values and 'amount' in log.new_values:
                try:
                    amount = float(log.new_values['amount'])
                    transaction_stats['total_amount_processed'] += amount
                except (ValueError, TypeError):
                    pass
        
        return transaction_stats
    
    @classmethod
    def _generate_security_report(cls, base_query) -> Dict[str, Any]:
        """Generate security section of audit report"""
        security_logs = base_query.filter(
            or_(
                AuditLog.action_type.like('%SECURITY%'),
                AuditLog.action_type.like('%LOGIN%'),
                AuditLog.action_type.like('%FAILED%')
            )
        ).all()
        
        security_stats = {
            'total_security_events': len(security_logs),
            'failed_logins': 0,
            'successful_logins': 0,
            'security_alerts': 0,
            'unique_ip_addresses': set(),
            'suspicious_activities': []
        }
        
        for log in security_logs:
            if log.ip_address:
                security_stats['unique_ip_addresses'].add(log.ip_address)
            
            if 'LOGIN_FAILED' in log.action_type:
                security_stats['failed_logins'] += 1
            elif 'LOGIN_SUCCESS' in log.action_type:
                security_stats['successful_logins'] += 1
            elif 'SECURITY' in log.action_type:
                security_stats['security_alerts'] += 1
                
                # Add to suspicious activities
                security_stats['suspicious_activities'].append({
                    'timestamp': log.created_at.isoformat(),
                    'action_type': log.action_type,
                    'user_id': log.user_id,
                    'ip_address': log.ip_address,
                    'details': log.new_values
                })
        
        security_stats['unique_ip_addresses'] = len(security_stats['unique_ip_addresses'])
        
        return security_stats
    
    @classmethod
    def _generate_system_report(cls, base_query) -> Dict[str, Any]:
        """Generate system section of audit report"""
        system_logs = base_query.filter(AuditLog.user_id.is_(None)).all()
        
        system_stats = {
            'total_system_events': len(system_logs),
            'system_errors': 0,
            'system_warnings': 0,
            'system_info': 0,
            'event_types': {}
        }
        
        for log in system_logs:
            action_type = log.action_type
            system_stats['event_types'][action_type] = \
                system_stats['event_types'].get(action_type, 0) + 1
            
            # Count by severity
            severity = log.new_values.get('severity', 'INFO') if log.new_values else 'INFO'
            if severity == 'ERROR':
                system_stats['system_errors'] += 1
            elif severity == 'WARNING':
                system_stats['system_warnings'] += 1
            else:
                system_stats['system_info'] += 1
        
        return system_stats
    
    @classmethod
    def _generate_compliance_summary(cls, base_query) -> Dict[str, Any]:
        """Generate compliance summary section"""
        all_logs = base_query.all()
        
        compliance_summary = {
            'total_audit_entries': len(all_logs),
            'data_integrity_checks': {
                'entries_with_timestamps': 0,
                'entries_with_user_context': 0,
                'entries_with_ip_tracking': 0
            },
            'retention_compliance': {
                'oldest_entry': None,
                'newest_entry': None,
                'retention_period_days': None
            },
            'audit_coverage': {
                'user_actions_logged': 0,
                'system_events_logged': 0,
                'transaction_events_logged': 0
            }
        }
        
        if all_logs:
            # Data integrity checks
            for log in all_logs:
                if log.created_at:
                    compliance_summary['data_integrity_checks']['entries_with_timestamps'] += 1
                if log.user_id:
                    compliance_summary['data_integrity_checks']['entries_with_user_context'] += 1
                if log.ip_address:
                    compliance_summary['data_integrity_checks']['entries_with_ip_tracking'] += 1
            
            # Retention compliance
            timestamps = [log.created_at for log in all_logs if log.created_at]
            if timestamps:
                compliance_summary['retention_compliance']['oldest_entry'] = min(timestamps).isoformat()
                compliance_summary['retention_compliance']['newest_entry'] = max(timestamps).isoformat()
                retention_period = max(timestamps) - min(timestamps)
                compliance_summary['retention_compliance']['retention_period_days'] = retention_period.days
            
            # Audit coverage
            for log in all_logs:
                if log.user_id:
                    compliance_summary['audit_coverage']['user_actions_logged'] += 1
                else:
                    compliance_summary['audit_coverage']['system_events_logged'] += 1
                
                if 'TRANSACTION' in log.action_type:
                    compliance_summary['audit_coverage']['transaction_events_logged'] += 1
        
        return compliance_summary
    
    @classmethod
    def cleanup_old_audit_logs(cls, retention_days: int = 2555) -> Dict[str, Any]:
        """
        Clean up old audit logs based on retention policy (default: 7 years)
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            Dictionary with cleanup results
        """
        cutoff_date = datetime.now(datetime.UTC) - timedelta(days=retention_days)
        
        # Count logs to be deleted
        logs_to_delete = AuditLog.query.filter(
            AuditLog.created_at < cutoff_date
        ).count()
        
        if logs_to_delete == 0:
            return {
                'success': True,
                'deleted_count': 0,
                'message': 'No logs found older than retention period'
            }
        
        try:
            # Log the cleanup operation
            cls.log_system_event(
                action_type='DATA_RETENTION_CLEANUP',
                details={
                    'retention_days': retention_days,
                    'cutoff_date': cutoff_date.isoformat(),
                    'logs_to_delete': logs_to_delete
                }
            )
            
            # Delete old logs
            deleted_count = AuditLog.query.filter(
                AuditLog.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_date.isoformat(),
                'message': f'Successfully deleted {deleted_count} old audit logs'
            }
            
        except Exception as e:
            db.session.rollback()
            
            # Log the error
            cls.log_system_event(
                action_type='DATA_RETENTION_CLEANUP_FAILED',
                details={
                    'error': str(e),
                    'retention_days': retention_days
                },
                severity='ERROR'
            )
            
            return {
                'success': False,
                'deleted_count': 0,
                'error': str(e),
                'message': 'Failed to clean up old audit logs'
            }
    
    @classmethod
    def get_audit_statistics(cls, days: int = 30) -> Dict[str, Any]:
        """
        Get audit statistics for a time period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with audit statistics
        """
        start_date = datetime.now(datetime.UTC) - timedelta(days=days)
        
        # Get logs in period
        logs = AuditLog.query.filter(AuditLog.created_at >= start_date).all()
        
        stats = {
            'period_days': days,
            'total_entries': len(logs),
            'user_actions': 0,
            'system_events': 0,
            'action_type_breakdown': {},
            'entity_type_breakdown': {},
            'user_activity': {},
            'daily_activity': {},
            'security_events': 0,
            'transaction_events': 0
        }
        
        for log in logs:
            # User vs system events
            if log.user_id:
                stats['user_actions'] += 1
                
                # User activity tracking
                if log.user_id not in stats['user_activity']:
                    stats['user_activity'][log.user_id] = {
                        'user_name': log.user.name if log.user else 'Unknown',
                        'action_count': 0
                    }
                stats['user_activity'][log.user_id]['action_count'] += 1
            else:
                stats['system_events'] += 1
            
            # Action type breakdown
            action_type = log.action_type
            stats['action_type_breakdown'][action_type] = \
                stats['action_type_breakdown'].get(action_type, 0) + 1
            
            # Entity type breakdown
            entity_type = log.entity_type
            stats['entity_type_breakdown'][entity_type] = \
                stats['entity_type_breakdown'].get(entity_type, 0) + 1
            
            # Daily activity
            day = log.created_at.date().isoformat()
            stats['daily_activity'][day] = stats['daily_activity'].get(day, 0) + 1
            
            # Special event counters
            if 'SECURITY' in action_type or 'LOGIN' in action_type:
                stats['security_events'] += 1
            
            if 'TRANSACTION' in action_type:
                stats['transaction_events'] += 1
        
        return stats
    
    @classmethod
    def verify_audit_integrity(cls) -> Dict[str, Any]:
        """
        Verify the integrity of audit logs
        
        Returns:
            Dictionary with integrity check results
        """
        integrity_results = {
            'total_logs_checked': 0,
            'integrity_issues': [],
            'missing_timestamps': 0,
            'missing_action_types': 0,
            'orphaned_user_references': 0,
            'data_consistency_issues': 0,
            'overall_status': 'HEALTHY'
        }
        
        # Get all audit logs
        all_logs = AuditLog.query.all()
        integrity_results['total_logs_checked'] = len(all_logs)
        
        for log in all_logs:
            # Check for missing timestamps
            if not log.created_at:
                integrity_results['missing_timestamps'] += 1
                integrity_results['integrity_issues'].append({
                    'log_id': log.id,
                    'issue': 'Missing timestamp',
                    'severity': 'HIGH'
                })
            
            # Check for missing action types
            if not log.action_type:
                integrity_results['missing_action_types'] += 1
                integrity_results['integrity_issues'].append({
                    'log_id': log.id,
                    'issue': 'Missing action type',
                    'severity': 'HIGH'
                })
            
            # Check for orphaned user references
            if log.user_id:
                user = User.query.get(log.user_id)
                if not user:
                    integrity_results['orphaned_user_references'] += 1
                    integrity_results['integrity_issues'].append({
                        'log_id': log.id,
                        'issue': f'Orphaned user reference: {log.user_id}',
                        'severity': 'MEDIUM'
                    })
            
            # Check data consistency
            if log.new_values:
                try:
                    if isinstance(log.new_values, str):
                        json.loads(log.new_values)
                except (json.JSONDecodeError, TypeError):
                    integrity_results['data_consistency_issues'] += 1
                    integrity_results['integrity_issues'].append({
                        'log_id': log.id,
                        'issue': 'Invalid JSON in new_values',
                        'severity': 'LOW'
                    })
        
        # Determine overall status
        total_issues = len(integrity_results['integrity_issues'])
        if total_issues == 0:
            integrity_results['overall_status'] = 'HEALTHY'
        elif total_issues < 10:
            integrity_results['overall_status'] = 'WARNING'
        else:
            integrity_results['overall_status'] = 'CRITICAL'
        
        return integrity_results