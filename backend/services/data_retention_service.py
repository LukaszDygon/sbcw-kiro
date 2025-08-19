"""
Data retention service for SoftBankCashWire
Handles data retention policy enforcement and cleanup
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import and_, or_, desc, func
from models import (
    db, User, Account, Transaction, EventAccount, MoneyRequest, 
    AuditLog, Notification, TransactionStatus, RequestStatus, EventStatus
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataRetentionService:
    """Service for managing data retention policies"""
    
    # Retention periods in days
    RETENTION_POLICIES = {
        'audit_logs': 2555,  # 7 years for financial audit compliance
        'completed_transactions': 2555,  # 7 years for financial records
        'failed_transactions': 365,  # 1 year for failed transactions
        'expired_money_requests': 90,  # 3 months for expired requests
        'closed_event_accounts': 1095,  # 3 years for closed events
        'user_notifications': 180,  # 6 months for notifications
        'inactive_user_sessions': 30,  # 30 days for session cleanup
        'temporary_files': 7,  # 1 week for temporary files
    }
    
    @classmethod
    def get_retention_policies(cls) -> Dict[str, int]:
        """
        Get current retention policies
        
        Returns:
            Dictionary of retention policies with days
        """
        return cls.RETENTION_POLICIES.copy()
    
    @classmethod
    def update_retention_policy(cls, policy_name: str, retention_days: int) -> Dict[str, Any]:
        """
        Update retention policy for specific data type
        
        Args:
            policy_name: Name of the retention policy
            retention_days: Number of days to retain data
            
        Returns:
            Dictionary with update result
        """
        try:
            if policy_name not in cls.RETENTION_POLICIES:
                return {
                    'success': False,
                    'error': f"Unknown retention policy: {policy_name}"
                }
            
            if retention_days < 1:
                return {
                    'success': False,
                    'error': "Retention period must be at least 1 day"
                }
            
            old_value = cls.RETENTION_POLICIES[policy_name]
            cls.RETENTION_POLICIES[policy_name] = retention_days
            
            logger.info(f"Updated retention policy {policy_name}: {old_value} -> {retention_days} days")
            
            return {
                'success': True,
                'policy_name': policy_name,
                'old_retention_days': old_value,
                'new_retention_days': retention_days
            }
            
        except Exception as e:
            logger.error(f"Failed to update retention policy: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def cleanup_expired_money_requests(cls) -> Dict[str, Any]:
        """
        Clean up expired money requests based on retention policy
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            retention_days = cls.RETENTION_POLICIES['expired_money_requests']
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Find expired money requests to clean up
            expired_requests = MoneyRequest.query.filter(
                and_(
                    or_(
                        MoneyRequest.status == RequestStatus.EXPIRED,
                        MoneyRequest.status == RequestStatus.DECLINED
                    ),
                    MoneyRequest.created_at < cutoff_date
                )
            ).all()
            
            cleaned_count = 0
            
            for request in expired_requests:
                try:
                    # Log the cleanup action
                    logger.info(f"Cleaning up expired money request: {request.id}")
                    
                    # Delete the request
                    db.session.delete(request)
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to delete money request {request.id}: {str(e)}")
                    continue
            
            if cleaned_count > 0:
                db.session.commit()
                logger.info(f"Cleaned up {cleaned_count} expired money requests")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup expired money requests: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def cleanup_old_notifications(cls) -> Dict[str, Any]:
        """
        Clean up old user notifications based on retention policy
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            retention_days = cls.RETENTION_POLICIES['user_notifications']
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Find old notifications to clean up
            old_notifications = Notification.query.filter(
                Notification.created_at < cutoff_date
            ).all()
            
            cleaned_count = 0
            
            for notification in old_notifications:
                try:
                    logger.info(f"Cleaning up old notification: {notification.id}")
                    db.session.delete(notification)
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to delete notification {notification.id}: {str(e)}")
                    continue
            
            if cleaned_count > 0:
                db.session.commit()
                logger.info(f"Cleaned up {cleaned_count} old notifications")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup old notifications: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def cleanup_failed_transactions(cls) -> Dict[str, Any]:
        """
        Clean up old failed transactions based on retention policy
        
        Returns:
            Dictionary with cleanup results
        """
        try:
            retention_days = cls.RETENTION_POLICIES['failed_transactions']
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Find failed transactions to clean up
            failed_transactions = Transaction.query.filter(
                and_(
                    Transaction.status == TransactionStatus.FAILED,
                    Transaction.created_at < cutoff_date
                )
            ).all()
            
            cleaned_count = 0
            
            for transaction in failed_transactions:
                try:
                    logger.info(f"Cleaning up failed transaction: {transaction.id}")
                    db.session.delete(transaction)
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to delete transaction {transaction.id}: {str(e)}")
                    continue
            
            if cleaned_count > 0:
                db.session.commit()
                logger.info(f"Cleaned up {cleaned_count} failed transactions")
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup failed transactions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def archive_old_audit_logs(cls) -> Dict[str, Any]:
        """
        Archive old audit logs (move to separate table or file)
        Note: For compliance, we don't delete audit logs, just archive them
        
        Returns:
            Dictionary with archival results
        """
        try:
            retention_days = cls.RETENTION_POLICIES['audit_logs']
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count audit logs that would be archived
            old_logs_count = AuditLog.query.filter(
                AuditLog.created_at < cutoff_date
            ).count()
            
            # For now, we just count them. In a production system,
            # you would move them to an archive table or export to files
            logger.info(f"Found {old_logs_count} audit logs older than {retention_days} days")
            
            return {
                'success': True,
                'logs_to_archive': old_logs_count,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat(),
                'note': 'Audit logs are counted but not deleted for compliance reasons'
            }
            
        except Exception as e:
            logger.error(f"Failed to process audit log archival: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def get_data_retention_status(cls) -> Dict[str, Any]:
        """
        Get current data retention status and statistics
        
        Returns:
            Dictionary with retention status information
        """
        try:
            status = {
                'retention_policies': cls.RETENTION_POLICIES.copy(),
                'data_counts': {},
                'cleanup_candidates': {}
            }
            
            # Count current data
            status['data_counts'] = {
                'total_transactions': Transaction.query.count(),
                'completed_transactions': Transaction.query.filter_by(status=TransactionStatus.COMPLETED).count(),
                'failed_transactions': Transaction.query.filter_by(status=TransactionStatus.FAILED).count(),
                'total_money_requests': MoneyRequest.query.count(),
                'expired_money_requests': MoneyRequest.query.filter(
                    or_(
                        MoneyRequest.status == RequestStatus.EXPIRED,
                        MoneyRequest.status == RequestStatus.DECLINED
                    )
                ).count(),
                'total_audit_logs': AuditLog.query.count(),
                'total_notifications': Notification.query.count(),
                'total_event_accounts': EventAccount.query.count(),
                'closed_event_accounts': EventAccount.query.filter_by(status=EventStatus.CLOSED).count()
            }
            
            # Count cleanup candidates
            for policy_name, retention_days in cls.RETENTION_POLICIES.items():
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                if policy_name == 'expired_money_requests':
                    count = MoneyRequest.query.filter(
                        and_(
                            or_(
                                MoneyRequest.status == RequestStatus.EXPIRED,
                                MoneyRequest.status == RequestStatus.DECLINED
                            ),
                            MoneyRequest.created_at < cutoff_date
                        )
                    ).count()
                elif policy_name == 'failed_transactions':
                    count = Transaction.query.filter(
                        and_(
                            Transaction.status == TransactionStatus.FAILED,
                            Transaction.created_at < cutoff_date
                        )
                    ).count()
                elif policy_name == 'user_notifications':
                    count = Notification.query.filter(
                        Notification.created_at < cutoff_date
                    ).count()
                elif policy_name == 'audit_logs':
                    count = AuditLog.query.filter(
                        AuditLog.created_at < cutoff_date
                    ).count()
                else:
                    count = 0
                
                status['cleanup_candidates'][policy_name] = {
                    'count': count,
                    'retention_days': retention_days,
                    'cutoff_date': cutoff_date.isoformat()
                }
            
            return {
                'success': True,
                'status': status,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get data retention status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def run_full_cleanup(cls) -> Dict[str, Any]:
        """
        Run full data cleanup based on all retention policies
        
        Returns:
            Dictionary with comprehensive cleanup results
        """
        try:
            results = {
                'success': True,
                'cleanup_results': {},
                'total_cleaned': 0,
                'errors': []
            }
            
            # Run individual cleanup operations
            cleanup_operations = [
                ('expired_money_requests', cls.cleanup_expired_money_requests),
                ('old_notifications', cls.cleanup_old_notifications),
                ('failed_transactions', cls.cleanup_failed_transactions),
                ('audit_logs_archive', cls.archive_old_audit_logs)
            ]
            
            for operation_name, operation_func in cleanup_operations:
                try:
                    result = operation_func()
                    results['cleanup_results'][operation_name] = result
                    
                    if result.get('success') and 'cleaned_count' in result:
                        results['total_cleaned'] += result['cleaned_count']
                    
                    if not result.get('success'):
                        results['errors'].append(f"{operation_name}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    error_msg = f"{operation_name}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(f"Cleanup operation failed: {error_msg}")
            
            # Overall success depends on whether any critical errors occurred
            results['success'] = len(results['errors']) == 0
            results['completed_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Full cleanup completed: {results['total_cleaned']} items cleaned, {len(results['errors'])} errors")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to run full cleanup: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def validate_retention_compliance(cls) -> Dict[str, Any]:
        """
        Validate that current data retention is compliant with policies
        
        Returns:
            Dictionary with compliance validation results
        """
        try:
            compliance_results = {
                'compliant': True,
                'violations': [],
                'warnings': [],
                'recommendations': []
            }
            
            status_result = cls.get_data_retention_status()
            if not status_result['success']:
                return {
                    'success': False,
                    'error': 'Failed to get retention status'
                }
            
            cleanup_candidates = status_result['status']['cleanup_candidates']
            
            # Check for compliance violations
            for policy_name, candidate_info in cleanup_candidates.items():
                count = candidate_info['count']
                retention_days = candidate_info['retention_days']
                
                if count > 0:
                    if policy_name in ['expired_money_requests', 'failed_transactions', 'user_notifications']:
                        # These should be cleaned up regularly
                        if count > 100:  # Threshold for violation
                            compliance_results['violations'].append({
                                'policy': policy_name,
                                'issue': f"{count} items exceed retention period of {retention_days} days",
                                'recommendation': f"Run cleanup for {policy_name}"
                            })
                            compliance_results['compliant'] = False
                        elif count > 50:  # Threshold for warning
                            compliance_results['warnings'].append({
                                'policy': policy_name,
                                'issue': f"{count} items approaching retention limit",
                                'recommendation': f"Consider running cleanup for {policy_name}"
                            })
                    
                    elif policy_name == 'audit_logs':
                        # Audit logs should be archived, not deleted
                        if count > 10000:  # Large number threshold
                            compliance_results['recommendations'].append({
                                'policy': policy_name,
                                'issue': f"{count} audit logs older than {retention_days} days",
                                'recommendation': "Consider archiving old audit logs to external storage"
                            })
            
            return {
                'success': True,
                'compliance': compliance_results,
                'checked_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to validate retention compliance: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }