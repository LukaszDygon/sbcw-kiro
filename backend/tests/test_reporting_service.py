"""
Tests for ReportingService
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from services.reporting_service import ReportingService
from models import (
    User, UserRole, Account, AccountStatus, Transaction, TransactionType, TransactionStatus,
    EventAccount, EventStatus, MoneyRequest, RequestStatus
)

class TestReportingService:
    """Test cases for ReportingService"""
    
    def test_generate_transaction_summary_report(self, app, db_session, sample_users, sample_accounts):
        """Test transaction summary report generation"""
        with app.app_context():
            # Create test transactions
            user1, user2 = sample_users[:2]
            account1, account2 = sample_accounts[:2]
            
            start_date = datetime.now(datetime.UTC) - timedelta(days=30)
            end_date = datetime.now(datetime.UTC)
            
            # Create transactions
            transaction1 = Transaction(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('100.00'),
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.COMPLETED,
                category='Food',
                created_at=start_date + timedelta(days=5)
            )
            
            transaction2 = Transaction(
                sender_id=user2.id,
                recipient_id=user1.id,
                amount=Decimal('50.00'),
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.COMPLETED,
                category='Entertainment',
                created_at=start_date + timedelta(days=10)
            )
            
            db_session.add_all([transaction1, transaction2])
            db_session.commit()
            
            # Generate report
            report = ReportingService.generate_transaction_summary_report(start_date, end_date)
            
            # Verify report structure
            assert report['report_type'] == 'TRANSACTION_SUMMARY'
            assert 'period' in report
            assert 'summary' in report
            assert 'category_breakdown' in report
            
            # Verify summary data
            assert report['summary']['total_transactions'] == 2
            assert Decimal(report['summary']['total_volume']) == Decimal('150.00')
            assert report['summary']['transfer_count'] == 2
            
            # Verify category breakdown
            categories = {cat['category']: cat for cat in report['category_breakdown']}
            assert 'Food' in categories
            assert 'Entertainment' in categories
            assert Decimal(categories['Food']['total_amount']) == Decimal('100.00')
            assert Decimal(categories['Entertainment']['total_amount']) == Decimal('50.00')
    
    def test_generate_user_activity_report(self, app, db_session, sample_users, sample_accounts):
        """Test user activity report generation"""
        with app.app_context():
            user1, user2 = sample_users[:2]
            
            start_date = datetime.now(datetime.UTC) - timedelta(days=30)
            end_date = datetime.now(datetime.UTC)
            
            # Create test transaction
            transaction = Transaction(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('75.00'),
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.COMPLETED,
                created_at=start_date + timedelta(days=5)
            )
            
            # Create test money request
            money_request = MoneyRequest(
                requester_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00'),
                description='Test request',
                status=RequestStatus.PENDING,
                created_at=start_date + timedelta(days=10)
            )
            
            db_session.add_all([transaction, money_request])
            db_session.commit()
            
            # Generate report
            report = ReportingService.generate_user_activity_report(start_date, end_date)
            
            # Verify report structure
            assert report['report_type'] == 'USER_ACTIVITY'
            assert 'user_activities' in report
            assert 'summary' in report
            
            # Find user1 in activities
            user1_activity = next(
                (u for u in report['user_activities'] if u['user_id'] == user1.id),
                None
            )
            assert user1_activity is not None
            assert user1_activity['transaction_activity']['sent_count'] == 1
            assert Decimal(user1_activity['transaction_activity']['total_sent']) == Decimal('75.00')
            assert user1_activity['request_activity']['sent_requests'] == 1
    
    def test_generate_event_account_report(self, app, db_session, sample_users):
        """Test event account report generation"""
        with app.app_context():
            user1 = sample_users[0]
            
            start_date = datetime.now(datetime.UTC) - timedelta(days=30)
            end_date = datetime.now(datetime.UTC)
            
            # Create test event
            event = EventAccount(
                name='Test Event',
                description='Test event description',
                target_amount=Decimal('500.00'),
                creator_id=user1.id,
                status=EventStatus.ACTIVE,
                created_at=start_date + timedelta(days=5)
            )
            db_session.add(event)
            db_session.commit()
            
            # Create contribution
            contribution = Transaction(
                sender_id=user1.id,
                amount=Decimal('100.00'),
                transaction_type=TransactionType.EVENT_CONTRIBUTION,
                status=TransactionStatus.COMPLETED,
                event_account_id=event.id,
                created_at=start_date + timedelta(days=10)
            )
            db_session.add(contribution)
            db_session.commit()
            
            # Generate report
            report = ReportingService.generate_event_account_report(start_date, end_date)
            
            # Verify report structure
            assert report['report_type'] == 'EVENT_ACCOUNT'
            assert 'events' in report
            assert 'summary' in report
            
            # Verify event data
            assert len(report['events']) == 1
            event_data = report['events'][0]
            assert event_data['event_name'] == 'Test Event'
            assert Decimal(event_data['target_amount']) == Decimal('500.00')
            assert Decimal(event_data['current_amount']) == Decimal('100.00')
            assert event_data['progress_percentage'] == 20.0
            assert event_data['contribution_count'] == 1
    
    def test_generate_personal_analytics(self, app, db_session, sample_users, sample_accounts):
        """Test personal analytics generation"""
        with app.app_context():
            user1, user2 = sample_users[:2]
            
            start_date = datetime.now(datetime.UTC) - timedelta(days=30)
            end_date = datetime.now(datetime.UTC)
            
            # Create test transactions
            transaction1 = Transaction(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('100.00'),
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.COMPLETED,
                category='Food',
                created_at=start_date + timedelta(days=5)
            )
            
            transaction2 = Transaction(
                sender_id=user2.id,
                recipient_id=user1.id,
                amount=Decimal('50.00'),
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.COMPLETED,
                category='Entertainment',
                created_at=start_date + timedelta(days=10)
            )
            
            db_session.add_all([transaction1, transaction2])
            db_session.commit()
            
            # Generate analytics
            analytics = ReportingService.generate_personal_analytics(user1.id, start_date, end_date)
            
            # Verify analytics structure
            assert analytics['report_type'] == 'PERSONAL_ANALYTICS'
            assert analytics['user_id'] == user1.id
            assert 'summary' in analytics
            assert 'spending_analysis' in analytics
            
            # Verify summary
            assert analytics['summary']['total_transactions'] == 2
            assert Decimal(analytics['summary']['total_sent']) == Decimal('100.00')
            assert Decimal(analytics['summary']['total_received']) == Decimal('50.00')
            assert Decimal(analytics['summary']['net_amount']) == Decimal('-50.00')
            
            # Verify spending categories
            categories = analytics['spending_analysis']['categories']
            assert len(categories) == 1  # Only sent transactions count for spending
            assert categories[0]['category'] == 'Food'
            assert Decimal(categories[0]['amount']) == Decimal('100.00')
    
    def test_export_to_csv(self, app):
        """Test CSV export functionality"""
        with app.app_context():
            # Create sample report data
            report_data = {
                'report_type': 'TRANSACTION_SUMMARY',
                'period': {
                    'start_date': '2024-01-01T00:00:00',
                    'end_date': '2024-01-31T23:59:59',
                    'duration_days': 31
                },
                'summary': {
                    'total_transactions': 10,
                    'total_volume': '1000.00'
                },
                'category_breakdown': [
                    {
                        'category': 'Food',
                        'transaction_count': 5,
                        'total_amount': '500.00',
                        'average_amount': '100.00',
                        'percentage_of_volume': 50.0
                    }
                ],
                'generated_at': '2024-01-31T12:00:00'
            }
            
            # Export to CSV
            csv_output = ReportingService.export_to_csv(report_data)
            
            # Verify CSV content
            assert 'Transaction Summary' in csv_output
            assert 'Food' in csv_output
            assert '500.00' in csv_output
            assert '50.00%' in csv_output
    
    def test_export_to_json(self, app):
        """Test JSON export functionality"""
        with app.app_context():
            # Create sample report data
            report_data = {
                'report_type': 'PERSONAL_ANALYTICS',
                'user_id': 'test-user-123',
                'summary': {
                    'total_transactions': 5,
                    'total_sent': '250.00'
                }
            }
            
            # Export to JSON
            json_output = ReportingService.export_to_json(report_data)
            
            # Verify JSON content
            assert '"report_type": "PERSONAL_ANALYTICS"' in json_output
            assert '"user_id": "test-user-123"' in json_output
            assert '"total_transactions": 5' in json_output
    
    def test_check_report_access(self, app):
        """Test report access control"""
        with app.app_context():
            # Admin should have access to all reports
            assert ReportingService.check_report_access(UserRole.ADMIN, 'USER_ACTIVITY') == True
            assert ReportingService.check_report_access(UserRole.ADMIN, 'TRANSACTION_SUMMARY') == True
            
            # Finance should have access to all reports
            assert ReportingService.check_report_access(UserRole.FINANCE, 'USER_ACTIVITY') == True
            assert ReportingService.check_report_access(UserRole.FINANCE, 'EVENT_ACCOUNT') == True
            
            # Employee should only access personal reports
            assert ReportingService.check_report_access(
                UserRole.EMPLOYEE, 'PERSONAL_ANALYTICS', 'user123', 'user123'
            ) == True
            assert ReportingService.check_report_access(
                UserRole.EMPLOYEE, 'PERSONAL_ANALYTICS', 'user123', 'user456'
            ) == False
            assert ReportingService.check_report_access(UserRole.EMPLOYEE, 'USER_ACTIVITY') == False
    
    def test_get_available_reports(self, app):
        """Test available reports by role"""
        with app.app_context():
            # Admin should see all reports
            admin_reports = ReportingService.get_available_reports(UserRole.ADMIN)
            assert len(admin_reports) == 4
            report_types = [r['type'] for r in admin_reports]
            assert 'TRANSACTION_SUMMARY' in report_types
            assert 'USER_ACTIVITY' in report_types
            assert 'EVENT_ACCOUNT' in report_types
            assert 'PERSONAL_ANALYTICS' in report_types
            
            # Employee should see limited reports
            employee_reports = ReportingService.get_available_reports(UserRole.EMPLOYEE)
            assert len(employee_reports) == 2
            employee_types = [r['type'] for r in employee_reports]
            assert 'TRANSACTION_SUMMARY' in employee_types
            assert 'PERSONAL_ANALYTICS' in employee_types
            assert 'USER_ACTIVITY' not in employee_types
    
    def test_validate_report_parameters(self, app, db_session, sample_users):
        """Test report parameter validation"""
        with app.app_context():
            user1 = sample_users[0]
            
            # Valid parameters
            valid_params = {
                'start_date': datetime.now(datetime.UTC) - timedelta(days=30),
                'end_date': datetime.now(datetime.UTC),
                'user_id': user1.id
            }
            
            result = ReportingService.validate_report_parameters('PERSONAL_ANALYTICS', valid_params)
            assert result['valid'] == True
            assert len(result['errors']) == 0
            
            # Invalid parameters - missing start_date
            invalid_params = {
                'end_date': datetime.now(datetime.UTC),
                'user_id': user1.id
            }
            
            result = ReportingService.validate_report_parameters('PERSONAL_ANALYTICS', invalid_params)
            assert result['valid'] == False
            assert 'start_date is required' in result['errors']
            
            # Invalid parameters - start_date after end_date
            invalid_params = {
                'start_date': datetime.now(datetime.UTC),
                'end_date': datetime.now(datetime.UTC) - timedelta(days=1),
                'user_id': user1.id
            }
            
            result = ReportingService.validate_report_parameters('PERSONAL_ANALYTICS', invalid_params)
            assert result['valid'] == False
            assert 'start_date must be before end_date' in result['errors']
            
            # Invalid parameters - non-existent user
            invalid_params = {
                'start_date': datetime.now(datetime.UTC) - timedelta(days=30),
                'end_date': datetime.now(datetime.UTC),
                'user_id': 'non-existent-user'
            }
            
            result = ReportingService.validate_report_parameters('PERSONAL_ANALYTICS', invalid_params)
            assert result['valid'] == False
            assert 'User non-existent-user not found' in result['errors']
    
    def test_generate_transaction_summary_report_user_specific(self, app, db_session, sample_users, sample_accounts):
        """Test user-specific transaction summary report"""
        with app.app_context():
            user1, user2, user3 = sample_users[:3]
            
            start_date = datetime.now(datetime.UTC) - timedelta(days=30)
            end_date = datetime.now(datetime.UTC)
            
            # Create transactions involving user1
            transaction1 = Transaction(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('100.00'),
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.COMPLETED,
                created_at=start_date + timedelta(days=5)
            )
            
            # Create transaction not involving user1
            transaction2 = Transaction(
                sender_id=user2.id,
                recipient_id=user3.id,
                amount=Decimal('50.00'),
                transaction_type=TransactionType.TRANSFER,
                status=TransactionStatus.COMPLETED,
                created_at=start_date + timedelta(days=10)
            )
            
            db_session.add_all([transaction1, transaction2])
            db_session.commit()
            
            # Generate user-specific report
            report = ReportingService.generate_transaction_summary_report(
                start_date, end_date, user1.id
            )
            
            # Should only include transactions involving user1
            assert report['summary']['total_transactions'] == 1
            assert Decimal(report['summary']['total_volume']) == Decimal('100.00')
            assert report['user_id'] == user1.id