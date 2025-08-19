"""
Reporting and analytics service for SoftBankCashWire
Handles comprehensive financial reports and system analytics
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, func, text
from models import (
    db, User, UserRole, Account, AccountStatus, Transaction, TransactionType, TransactionStatus,
    EventAccount, EventStatus, MoneyRequest, RequestStatus, AuditLog
)
from services.pdf_export_service import PDFExportService
import csv
import io
import json

class ReportingService:
    """Service for generating reports and analytics"""
    
    @classmethod
    def generate_transaction_summary_report(cls, start_date: datetime, end_date: datetime,
                                          user_id: str = None) -> Dict[str, Any]:
        """
        Generate transaction summary report
        
        Args:
            start_date: Report start date
            end_date: Report end date
            user_id: Optional user ID for user-specific report
            
        Returns:
            Dictionary with transaction summary data
        """
        # Base query for transactions in period
        query = Transaction.query.filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == TransactionStatus.COMPLETED
        )
        
        # Filter by user if specified
        if user_id:
            query = query.filter(
                or_(
                    Transaction.sender_id == user_id,
                    Transaction.recipient_id == user_id
                )
            )
        
        transactions = query.all()
        
        # Calculate summary statistics
        total_transactions = len(transactions)
        total_volume = sum(t.amount for t in transactions) or Decimal('0.00')
        
        # Group by transaction type
        transfers = [t for t in transactions if t.transaction_type == TransactionType.TRANSFER]
        event_contributions = [t for t in transactions if t.transaction_type == TransactionType.EVENT_CONTRIBUTION]
        
        # Calculate averages
        avg_transaction_amount = (total_volume / total_transactions) if total_transactions > 0 else Decimal('0.00')
        avg_transfer_amount = (sum(t.amount for t in transfers) / len(transfers)) if transfers else Decimal('0.00')
        avg_contribution_amount = (sum(t.amount for t in event_contributions) / len(event_contributions)) if event_contributions else Decimal('0.00')
        
        # Group by category
        category_breakdown = {}
        for transaction in transactions:
            category = transaction.category or 'Uncategorized'
            if category not in category_breakdown:
                category_breakdown[category] = {
                    'count': 0,
                    'total_amount': Decimal('0.00')
                }
            category_breakdown[category]['count'] += 1
            category_breakdown[category]['total_amount'] += transaction.amount
        
        # Convert to list and sort by amount
        categories = [
            {
                'category': category,
                'transaction_count': data['count'],
                'total_amount': str(data['total_amount']),
                'average_amount': str(data['total_amount'] / data['count']) if data['count'] > 0 else '0.00',
                'percentage_of_volume': float((data['total_amount'] / total_volume) * 100) if total_volume > 0 else 0
            }
            for category, data in category_breakdown.items()
        ]
        categories.sort(key=lambda x: Decimal(x['total_amount']), reverse=True)
        
        return {
            'report_type': 'TRANSACTION_SUMMARY',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'user_id': user_id,
            'summary': {
                'total_transactions': total_transactions,
                'total_volume': str(total_volume),
                'average_transaction_amount': str(avg_transaction_amount),
                'transfer_count': len(transfers),
                'event_contribution_count': len(event_contributions),
                'average_transfer_amount': str(avg_transfer_amount),
                'average_contribution_amount': str(avg_contribution_amount)
            },
            'category_breakdown': categories,
            'generated_at': datetime.now(datetime.UTC).isoformat()
        }    

    @classmethod
    def generate_user_activity_report(cls, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate user activity report
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary with user activity data
        """
        # Get all users
        users = User.query.filter_by(account_status=AccountStatus.ACTIVE).all()
        
        user_activities = []
        
        for user in users:
            # Get user's transactions in period
            user_transactions = Transaction.query.filter(
                or_(
                    Transaction.sender_id == user.id,
                    Transaction.recipient_id == user.id
                ),
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date,
                Transaction.status == TransactionStatus.COMPLETED
            ).all()
            
            # Calculate user statistics
            sent_transactions = [t for t in user_transactions if t.sender_id == user.id]
            received_transactions = [t for t in user_transactions if t.recipient_id == user.id]
            
            total_sent = sum(t.amount for t in sent_transactions) or Decimal('0.00')
            total_received = sum(t.amount for t in received_transactions) or Decimal('0.00')
            
            # Get user's money requests
            sent_requests = MoneyRequest.query.filter(
                MoneyRequest.requester_id == user.id,
                MoneyRequest.created_at >= start_date,
                MoneyRequest.created_at <= end_date
            ).count()
            
            received_requests = MoneyRequest.query.filter(
                MoneyRequest.recipient_id == user.id,
                MoneyRequest.created_at >= start_date,
                MoneyRequest.created_at <= end_date
            ).count()
            
            # Get user's event activities
            created_events = EventAccount.query.filter(
                EventAccount.creator_id == user.id,
                EventAccount.created_at >= start_date,
                EventAccount.created_at <= end_date
            ).count()
            
            event_contributions = Transaction.query.filter(
                Transaction.sender_id == user.id,
                Transaction.transaction_type == TransactionType.EVENT_CONTRIBUTION,
                Transaction.created_at >= start_date,
                Transaction.created_at <= end_date,
                Transaction.status == TransactionStatus.COMPLETED
            ).count()
            
            # Get current balance
            current_balance = user.account.balance if user.account else Decimal('0.00')
            
            user_activities.append({
                'user_id': user.id,
                'user_name': user.name,
                'user_email': user.email,
                'user_role': user.role.value,
                'current_balance': str(current_balance),
                'transaction_activity': {
                    'total_transactions': len(user_transactions),
                    'sent_count': len(sent_transactions),
                    'received_count': len(received_transactions),
                    'total_sent': str(total_sent),
                    'total_received': str(total_received),
                    'net_amount': str(total_received - total_sent)
                },
                'request_activity': {
                    'sent_requests': sent_requests,
                    'received_requests': received_requests
                },
                'event_activity': {
                    'created_events': created_events,
                    'event_contributions': event_contributions
                },
                'last_login': user.last_login.isoformat() if user.last_login else None
            })
        
        # Sort by total transaction volume
        user_activities.sort(
            key=lambda x: Decimal(x['transaction_activity']['total_sent']) + Decimal(x['transaction_activity']['total_received']),
            reverse=True
        )
        
        return {
            'report_type': 'USER_ACTIVITY',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'summary': {
                'total_users': len(user_activities),
                'active_users': len([u for u in user_activities if u['transaction_activity']['total_transactions'] > 0])
            },
            'user_activities': user_activities,
            'generated_at': datetime.now(datetime.UTC).isoformat()
        }

    @classmethod
    def generate_event_account_report(cls, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate event account report with funding statistics
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary with event account data
        """
        # Get all event accounts in period
        events = EventAccount.query.filter(
            EventAccount.created_at >= start_date,
            EventAccount.created_at <= end_date
        ).all()
        
        event_data = []
        total_target_amount = Decimal('0.00')
        total_raised_amount = Decimal('0.00')
        
        for event in events:
            # Get contributions for this event
            contributions = Transaction.query.filter(
                Transaction.event_account_id == event.id,
                Transaction.transaction_type == TransactionType.EVENT_CONTRIBUTION,
                Transaction.status == TransactionStatus.COMPLETED
            ).all()
            
            total_contributions = sum(c.amount for c in contributions) or Decimal('0.00')
            contribution_count = len(contributions)
            
            # Get unique contributors
            contributor_ids = set(c.sender_id for c in contributions)
            unique_contributors = len(contributor_ids)
            
            # Calculate progress
            progress_percentage = float((total_contributions / event.target_amount) * 100) if event.target_amount > 0 else 0
            
            # Calculate average contribution
            avg_contribution = (total_contributions / contribution_count) if contribution_count > 0 else Decimal('0.00')
            
            event_data.append({
                'event_id': event.id,
                'event_name': event.name,
                'event_description': event.description,
                'creator_id': event.creator_id,
                'creator_name': event.creator.name if event.creator else 'Unknown',
                'status': event.status.value,
                'target_amount': str(event.target_amount),
                'current_amount': str(total_contributions),
                'remaining_amount': str(event.target_amount - total_contributions),
                'progress_percentage': round(progress_percentage, 2),
                'contribution_count': contribution_count,
                'unique_contributors': unique_contributors,
                'average_contribution': str(avg_contribution),
                'created_at': event.created_at.isoformat(),
                'deadline': event.deadline.isoformat() if event.deadline else None,
                'is_expired': event.deadline < datetime.now(datetime.UTC) if event.deadline else False
            })
            
            total_target_amount += event.target_amount
            total_raised_amount += total_contributions
        
        # Sort by progress percentage (descending)
        event_data.sort(key=lambda x: x['progress_percentage'], reverse=True)
        
        # Calculate summary statistics
        active_events = len([e for e in event_data if e['status'] == EventStatus.ACTIVE.value])
        completed_events = len([e for e in event_data if e['status'] == EventStatus.COMPLETED.value])
        expired_events = len([e for e in event_data if e['is_expired']])
        
        overall_progress = float((total_raised_amount / total_target_amount) * 100) if total_target_amount > 0 else 0
        
        return {
            'report_type': 'EVENT_ACCOUNT',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'summary': {
                'total_events': len(event_data),
                'active_events': active_events,
                'completed_events': completed_events,
                'expired_events': expired_events,
                'total_target_amount': str(total_target_amount),
                'total_raised_amount': str(total_raised_amount),
                'overall_progress_percentage': round(overall_progress, 2)
            },
            'events': event_data,
            'generated_at': datetime.now(datetime.UTC).isoformat()
        }

    @classmethod
    def generate_personal_analytics(cls, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate personal analytics dashboard for a user
        
        Args:
            user_id: User ID for analytics
            start_date: Analytics start date
            end_date: Analytics end date
            
        Returns:
            Dictionary with personal analytics data
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get user's transactions
        transactions = Transaction.query.filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == TransactionStatus.COMPLETED
        ).all()
        
        sent_transactions = [t for t in transactions if t.sender_id == user_id]
        received_transactions = [t for t in transactions if t.recipient_id == user_id]
        
        # Calculate spending by category
        spending_by_category = {}
        for transaction in sent_transactions:
            category = transaction.category or 'Uncategorized'
            if category not in spending_by_category:
                spending_by_category[category] = Decimal('0.00')
            spending_by_category[category] += transaction.amount
        
        # Convert to list and sort
        spending_categories = [
            {
                'category': category,
                'amount': str(amount),
                'percentage': float((amount / sum(spending_by_category.values())) * 100) if spending_by_category else 0
            }
            for category, amount in spending_by_category.items()
        ]
        spending_categories.sort(key=lambda x: Decimal(x['amount']), reverse=True)
        
        # Calculate monthly trends
        monthly_data = {}
        for transaction in transactions:
            month_key = transaction.created_at.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'sent': Decimal('0.00'),
                    'received': Decimal('0.00'),
                    'net': Decimal('0.00')
                }
            
            if transaction.sender_id == user_id:
                monthly_data[month_key]['sent'] += transaction.amount
                monthly_data[month_key]['net'] -= transaction.amount
            else:
                monthly_data[month_key]['received'] += transaction.amount
                monthly_data[month_key]['net'] += transaction.amount
        
        monthly_trends = [
            {
                'month': month,
                'sent': str(data['sent']),
                'received': str(data['received']),
                'net': str(data['net'])
            }
            for month, data in sorted(monthly_data.items())
        ]
        
        # Get money request statistics
        sent_requests = MoneyRequest.query.filter(
            MoneyRequest.requester_id == user_id,
            MoneyRequest.created_at >= start_date,
            MoneyRequest.created_at <= end_date
        ).all()
        
        received_requests = MoneyRequest.query.filter(
            MoneyRequest.recipient_id == user_id,
            MoneyRequest.created_at >= start_date,
            MoneyRequest.created_at <= end_date
        ).all()
        
        # Get event participation
        created_events = EventAccount.query.filter(
            EventAccount.creator_id == user_id,
            EventAccount.created_at >= start_date,
            EventAccount.created_at <= end_date
        ).count()
        
        event_contributions = Transaction.query.filter(
            Transaction.sender_id == user_id,
            Transaction.transaction_type == TransactionType.EVENT_CONTRIBUTION,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date,
            Transaction.status == TransactionStatus.COMPLETED
        ).all()
        
        total_sent = sum(t.amount for t in sent_transactions) or Decimal('0.00')
        total_received = sum(t.amount for t in received_transactions) or Decimal('0.00')
        total_contributions = sum(t.amount for t in event_contributions) or Decimal('0.00')
        
        return {
            'report_type': 'PERSONAL_ANALYTICS',
            'user_id': user_id,
            'user_name': user.name,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'summary': {
                'total_transactions': len(transactions),
                'total_sent': str(total_sent),
                'total_received': str(total_received),
                'net_amount': str(total_received - total_sent),
                'current_balance': str(user.account.balance) if user.account else '0.00'
            },
            'spending_analysis': {
                'categories': spending_categories,
                'monthly_trends': monthly_trends
            },
            'money_requests': {
                'sent_count': len(sent_requests),
                'received_count': len(received_requests),
                'approved_sent': len([r for r in sent_requests if r.status == RequestStatus.APPROVED]),
                'approved_received': len([r for r in received_requests if r.status == RequestStatus.APPROVED])
            },
            'event_participation': {
                'created_events': created_events,
                'contributions_count': len(event_contributions),
                'total_contributed': str(total_contributions)
            },
            'generated_at': datetime.now(datetime.UTC).isoformat()
        }
    
    @classmethod
    def export_to_csv(cls, report_data: Dict[str, Any]) -> str:
        """
        Export report data to CSV format
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        
        if report_data['report_type'] == 'TRANSACTION_SUMMARY':
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Report Type', 'Transaction Summary'])
            writer.writerow(['Period', f"{report_data['period']['start_date']} to {report_data['period']['end_date']}"])
            writer.writerow(['Generated At', report_data['generated_at']])
            writer.writerow([])  # Empty row
            
            # Write summary
            writer.writerow(['Summary'])
            for key, value in report_data['summary'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])  # Empty row
            
            # Write category breakdown
            writer.writerow(['Category Breakdown'])
            writer.writerow(['Category', 'Transaction Count', 'Total Amount', 'Average Amount', 'Percentage of Volume'])
            for category in report_data['category_breakdown']:
                writer.writerow([
                    category['category'],
                    category['transaction_count'],
                    category['total_amount'],
                    category['average_amount'],
                    f"{category['percentage_of_volume']:.2f}%"
                ])
        
        elif report_data['report_type'] == 'USER_ACTIVITY':
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Report Type', 'User Activity'])
            writer.writerow(['Period', f"{report_data['period']['start_date']} to {report_data['period']['end_date']}"])
            writer.writerow(['Generated At', report_data['generated_at']])
            writer.writerow([])  # Empty row
            
            # Write user activities
            writer.writerow(['User Activities'])
            writer.writerow([
                'User ID', 'Name', 'Email', 'Role', 'Current Balance',
                'Total Transactions', 'Sent Count', 'Received Count',
                'Total Sent', 'Total Received', 'Net Amount',
                'Sent Requests', 'Received Requests',
                'Created Events', 'Event Contributions', 'Last Login'
            ])
            
            for user in report_data['user_activities']:
                writer.writerow([
                    user['user_id'],
                    user['user_name'],
                    user['user_email'],
                    user['user_role'],
                    user['current_balance'],
                    user['transaction_activity']['total_transactions'],
                    user['transaction_activity']['sent_count'],
                    user['transaction_activity']['received_count'],
                    user['transaction_activity']['total_sent'],
                    user['transaction_activity']['total_received'],
                    user['transaction_activity']['net_amount'],
                    user['request_activity']['sent_requests'],
                    user['request_activity']['received_requests'],
                    user['event_activity']['created_events'],
                    user['event_activity']['event_contributions'],
                    user['last_login'] or 'Never'
                ])
        
        elif report_data['report_type'] == 'EVENT_ACCOUNT':
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Report Type', 'Event Account'])
            writer.writerow(['Period', f"{report_data['period']['start_date']} to {report_data['period']['end_date']}"])
            writer.writerow(['Generated At', report_data['generated_at']])
            writer.writerow([])  # Empty row
            
            # Write events
            writer.writerow(['Event Accounts'])
            writer.writerow([
                'Event ID', 'Name', 'Description', 'Creator', 'Status',
                'Target Amount', 'Current Amount', 'Remaining Amount',
                'Progress %', 'Contribution Count', 'Unique Contributors',
                'Average Contribution', 'Created At', 'Deadline', 'Is Expired'
            ])
            
            for event in report_data['events']:
                writer.writerow([
                    event['event_id'],
                    event['event_name'],
                    event['event_description'],
                    event['creator_name'],
                    event['status'],
                    event['target_amount'],
                    event['current_amount'],
                    event['remaining_amount'],
                    f"{event['progress_percentage']}%",
                    event['contribution_count'],
                    event['unique_contributors'],
                    event['average_contribution'],
                    event['created_at'],
                    event['deadline'] or 'No deadline',
                    'Yes' if event['is_expired'] else 'No'
                ])
        
        elif report_data['report_type'] == 'PERSONAL_ANALYTICS':
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Report Type', 'Personal Analytics'])
            writer.writerow(['User', report_data['user_name']])
            writer.writerow(['Period', f"{report_data['period']['start_date']} to {report_data['period']['end_date']}"])
            writer.writerow(['Generated At', report_data['generated_at']])
            writer.writerow([])  # Empty row
            
            # Write summary
            writer.writerow(['Summary'])
            for key, value in report_data['summary'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])  # Empty row
            
            # Write spending categories
            writer.writerow(['Spending by Category'])
            writer.writerow(['Category', 'Amount', 'Percentage'])
            for category in report_data['spending_analysis']['categories']:
                writer.writerow([
                    category['category'],
                    category['amount'],
                    f"{category['percentage']:.2f}%"
                ])
            writer.writerow([])  # Empty row
            
            # Write monthly trends
            writer.writerow(['Monthly Trends'])
            writer.writerow(['Month', 'Sent', 'Received', 'Net'])
            for month in report_data['spending_analysis']['monthly_trends']:
                writer.writerow([
                    month['month'],
                    month['sent'],
                    month['received'],
                    month['net']
                ])
        
        return output.getvalue()

    @classmethod
    def export_to_json(cls, report_data: Dict[str, Any]) -> str:
        """
        Export report data to JSON format
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            JSON string
        """
        return json.dumps(report_data, indent=2, default=str)
    
    @classmethod
    def export_to_pdf(cls, report_data: Dict[str, Any]) -> bytes:
        """
        Export report data to PDF format
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            PDF bytes
        """
        report_type = report_data.get('report_type')
        
        if report_type == 'TRANSACTION_SUMMARY':
            return PDFExportService.generate_transaction_summary_pdf(report_data)
        elif report_type == 'USER_ACTIVITY':
            return PDFExportService.generate_user_activity_pdf(report_data)
        elif report_type == 'EVENT_ACCOUNT':
            return PDFExportService.generate_event_account_pdf(report_data)
        elif report_type == 'PERSONAL_ANALYTICS':
            return PDFExportService.generate_personal_analytics_pdf(report_data)
        else:
            raise ValueError(f"Unsupported report type for PDF export: {report_type}")

    @classmethod
    def check_report_access(cls, user_role: UserRole, report_type: str, target_user_id: str = None, 
                          requesting_user_id: str = None) -> bool:
        """
        Check if user has access to generate specific report
        
        Args:
            user_role: Role of requesting user
            report_type: Type of report being requested
            target_user_id: User ID for user-specific reports
            requesting_user_id: ID of user making the request
            
        Returns:
            Boolean indicating access permission
        """
        # Admin and Finance roles have access to all reports
        if user_role in [UserRole.ADMIN, UserRole.FINANCE]:
            return True
        
        # Employee role restrictions
        if user_role == UserRole.EMPLOYEE:
            # Can only access personal analytics for themselves
            if report_type == 'PERSONAL_ANALYTICS':
                return target_user_id == requesting_user_id
            
            # Can access transaction summary for their own transactions
            if report_type == 'TRANSACTION_SUMMARY':
                return target_user_id == requesting_user_id
            
            # Cannot access system-wide reports
            if report_type in ['USER_ACTIVITY', 'EVENT_ACCOUNT']:
                return False
        
        return False

    @classmethod
    def get_available_reports(cls, user_role: UserRole) -> List[Dict[str, Any]]:
        """
        Get list of available reports for user role
        
        Args:
            user_role: User role
            
        Returns:
            List of available report types with descriptions
        """
        all_reports = [
            {
                'type': 'TRANSACTION_SUMMARY',
                'name': 'Transaction Summary',
                'description': 'Summary of transaction activity and spending patterns',
                'parameters': ['start_date', 'end_date', 'user_id (optional)']
            },
            {
                'type': 'USER_ACTIVITY',
                'name': 'User Activity Report',
                'description': 'Comprehensive user activity and engagement metrics',
                'parameters': ['start_date', 'end_date']
            },
            {
                'type': 'EVENT_ACCOUNT',
                'name': 'Event Account Report',
                'description': 'Event funding statistics and progress tracking',
                'parameters': ['start_date', 'end_date']
            },
            {
                'type': 'PERSONAL_ANALYTICS',
                'name': 'Personal Analytics',
                'description': 'Individual user spending analysis and trends',
                'parameters': ['user_id', 'start_date', 'end_date']
            }
        ]
        
        if user_role in [UserRole.ADMIN, UserRole.FINANCE]:
            return all_reports
        elif user_role == UserRole.EMPLOYEE:
            return [r for r in all_reports if r['type'] in ['TRANSACTION_SUMMARY', 'PERSONAL_ANALYTICS']]
        
        return []

    @classmethod
    def validate_report_parameters(cls, report_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate report parameters
        
        Args:
            report_type: Type of report
            parameters: Report parameters
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        # Common validations
        if 'start_date' not in parameters:
            errors.append('start_date is required')
        elif not isinstance(parameters['start_date'], datetime):
            errors.append('start_date must be a datetime object')
        
        if 'end_date' not in parameters:
            errors.append('end_date is required')
        elif not isinstance(parameters['end_date'], datetime):
            errors.append('end_date must be a datetime object')
        
        if 'start_date' in parameters and 'end_date' in parameters:
            if isinstance(parameters['start_date'], datetime) and isinstance(parameters['end_date'], datetime):
                if parameters['start_date'] >= parameters['end_date']:
                    errors.append('start_date must be before end_date')
                
                # Check for reasonable date range (max 2 years)
                if (parameters['end_date'] - parameters['start_date']).days > 730:
                    errors.append('Date range cannot exceed 2 years')
        
        # Report-specific validations
        if report_type == 'PERSONAL_ANALYTICS':
            if 'user_id' not in parameters:
                errors.append('user_id is required for personal analytics')
            elif parameters['user_id']:
                user = User.query.get(parameters['user_id'])
                if not user:
                    errors.append(f"User {parameters['user_id']} not found")
        
        if report_type == 'TRANSACTION_SUMMARY' and 'user_id' in parameters and parameters['user_id']:
            user = User.query.get(parameters['user_id'])
            if not user:
                errors.append(f"User {parameters['user_id']} not found")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }