"""
Tests for Reporting API endpoints
"""
import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from models import (
    User, UserRole, Account, Transaction, TransactionType, TransactionStatus,
    EventAccount, EventStatus
)

class TestReportingAPI:
    """Test cases for Reporting API endpoints"""
    
    def test_get_available_reports_admin(self, client, admin_headers):
        """Test getting available reports as admin"""
        response = client.get('/api/reporting/available', headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['reports']) == 4
        
        report_types = [r['type'] for r in data['reports']]
        assert 'TRANSACTION_SUMMARY' in report_types
        assert 'USER_ACTIVITY' in report_types
        assert 'EVENT_ACCOUNT' in report_types
        assert 'PERSONAL_ANALYTICS' in report_types
    
    def test_get_available_reports_employee(self, client, employee_headers):
        """Test getting available reports as employee"""
        response = client.get('/api/reporting/available', headers=employee_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['reports']) == 2
        
        report_types = [r['type'] for r in data['reports']]
        assert 'TRANSACTION_SUMMARY' in report_types
        assert 'PERSONAL_ANALYTICS' in report_types
        assert 'USER_ACTIVITY' not in report_types
    
    def test_get_available_reports_unauthorized(self, client):
        """Test getting available reports without authentication"""
        response = client.get('/api/reporting/available')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'Authentication required'
    
    def test_generate_transaction_summary_admin(self, client, admin_headers, db_session, sample_users, sample_accounts):
        """Test generating transaction summary as admin"""
        # Create test transactions
        user1, user2 = sample_users[:2]
        
        transaction = Transaction(
            sender_id=user1.id,
            recipient_id=user2.id,
            amount=Decimal('100.00'),
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            category='Food',
            created_at=datetime.now(datetime.UTC) - timedelta(days=5)
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Generate report
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/reporting/transaction-summary', 
                             headers=admin_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        assert data['data']['report_type'] == 'TRANSACTION_SUMMARY'
        assert data['data']['summary']['total_transactions'] == 1
    
    def test_generate_transaction_summary_user_specific(self, client, admin_headers, db_session, sample_users, sample_accounts):
        """Test generating user-specific transaction summary"""
        user1, user2, user3 = sample_users[:3]
        
        # Create transactions
        transaction1 = Transaction(
            sender_id=user1.id,
            recipient_id=user2.id,
            amount=Decimal('100.00'),
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(datetime.UTC) - timedelta(days=5)
        )
        
        transaction2 = Transaction(
            sender_id=user2.id,
            recipient_id=user3.id,
            amount=Decimal('50.00'),
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(datetime.UTC) - timedelta(days=3)
        )
        
        db_session.add_all([transaction1, transaction2])
        db_session.commit()
        
        # Generate user-specific report
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/reporting/transaction-summary',
                             headers=admin_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date,
                                 'user_id': user1.id
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['summary']['total_transactions'] == 1
        assert data['data']['user_id'] == user1.id
    
    def test_generate_transaction_summary_csv_export(self, client, admin_headers, db_session, sample_users, sample_accounts):
        """Test CSV export of transaction summary"""
        user1, user2 = sample_users[:2]
        
        transaction = Transaction(
            sender_id=user1.id,
            recipient_id=user2.id,
            amount=Decimal('100.00'),
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            category='Food',
            created_at=datetime.now(datetime.UTC) - timedelta(days=5)
        )
        db_session.add(transaction)
        db_session.commit()
        
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/reporting/transaction-summary',
                             headers=admin_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date,
                                 'export_format': 'csv'
                             })
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        assert 'attachment' in response.headers['Content-Disposition']
        assert 'Transaction Summary' in response.data.decode()
    
    def test_generate_user_activity_report(self, client, admin_headers, db_session, sample_users, sample_accounts):
        """Test generating user activity report"""
        user1, user2 = sample_users[:2]
        
        transaction = Transaction(
            sender_id=user1.id,
            recipient_id=user2.id,
            amount=Decimal('75.00'),
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(datetime.UTC) - timedelta(days=5)
        )
        db_session.add(transaction)
        db_session.commit()
        
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/reporting/user-activity',
                             headers=admin_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['report_type'] == 'USER_ACTIVITY'
        assert 'user_activities' in data['data']
    
    def test_generate_user_activity_report_employee_denied(self, client, employee_headers):
        """Test employee access denied for user activity report"""
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/reporting/user-activity',
                             headers=employee_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Access denied' in data['error']
    
    def test_generate_event_account_report(self, client, admin_headers, db_session, sample_users):
        """Test generating event account report"""
        user1 = sample_users[0]
        
        # Create test event
        event = EventAccount(
            name='Test Event',
            description='Test event description',
            target_amount=Decimal('500.00'),
            creator_id=user1.id,
            status=EventStatus.ACTIVE,
            created_at=datetime.now(datetime.UTC) - timedelta(days=10)
        )
        db_session.add(event)
        db_session.commit()
        
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/reporting/event-accounts',
                             headers=admin_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['report_type'] == 'EVENT_ACCOUNT'
        assert len(data['data']['events']) == 1
        assert data['data']['events'][0]['event_name'] == 'Test Event'
    
    def test_generate_personal_analytics(self, client, employee_headers, db_session, sample_users, sample_accounts):
        """Test generating personal analytics"""
        user1, user2 = sample_users[:2]
        
        # Create test transactions
        transaction1 = Transaction(
            sender_id=user1.id,
            recipient_id=user2.id,
            amount=Decimal('100.00'),
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            category='Food',
            created_at=datetime.now(datetime.UTC) - timedelta(days=5)
        )
        
        transaction2 = Transaction(
            sender_id=user2.id,
            recipient_id=user1.id,
            amount=Decimal('50.00'),
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            category='Entertainment',
            created_at=datetime.now(datetime.UTC) - timedelta(days=3)
        )
        
        db_session.add_all([transaction1, transaction2])
        db_session.commit()
        
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/reporting/personal-analytics',
                             headers=employee_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['report_type'] == 'PERSONAL_ANALYTICS'
        assert 'spending_analysis' in data['data']
    
    def test_generate_personal_analytics_other_user_denied(self, client, employee_headers, sample_users):
        """Test employee cannot access other user's analytics"""
        user2 = sample_users[1]
        
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/reporting/personal-analytics',
                             headers=employee_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date,
                                 'user_id': user2.id
                             })
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Access denied' in data['error']
    
    def test_invalid_date_format(self, client, admin_headers):
        """Test invalid date format handling"""
        response = client.post('/api/reporting/transaction-summary',
                             headers=admin_headers,
                             json={
                                 'start_date': 'invalid-date',
                                 'end_date': datetime.now(datetime.UTC).isoformat()
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Invalid start_date format' in data['error']
    
    def test_missing_required_parameters(self, client, admin_headers):
        """Test missing required parameters"""
        response = client.post('/api/reporting/transaction-summary',
                             headers=admin_headers,
                             json={
                                 'start_date': datetime.now(datetime.UTC).isoformat()
                                 # Missing end_date
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'errors' in data
    
    def test_date_range_validation(self, client, admin_headers):
        """Test date range validation"""
        end_date = datetime.now(datetime.UTC)
        start_date = end_date + timedelta(days=1)  # Start after end
        
        response = client.post('/api/reporting/transaction-summary',
                             headers=admin_headers,
                             json={
                                 'start_date': start_date.isoformat(),
                                 'end_date': end_date.isoformat()
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'start_date must be before end_date' in data['errors']
    
    def test_health_check(self, client):
        """Test reporting service health check"""
        response = client.get('/api/reporting/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['service'] == 'reporting'
        assert data['status'] == 'healthy'
    
    def test_json_export_format(self, client, admin_headers, db_session, sample_users, sample_accounts):
        """Test JSON export format"""
        user1, user2 = sample_users[:2]
        
        transaction = Transaction(
            sender_id=user1.id,
            recipient_id=user2.id,
            amount=Decimal('100.00'),
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(datetime.UTC) - timedelta(days=5)
        )
        db_session.add(transaction)
        db_session.commit()
        
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/reporting/transaction-summary',
                             headers=admin_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date,
                                 'export_format': 'json'
                             })
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        assert 'attachment' in response.headers['Content-Disposition']
        
        # Verify it's valid JSON
        data = json.loads(response.data)
        assert data['report_type'] == 'TRANSACTION_SUMMARY'