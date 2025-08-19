"""
Comprehensive API integration tests for SoftBankCashWire
Tests all endpoints with proper authentication and validation
"""
import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from models import User, UserRole, Account, Transaction, TransactionStatus, EventAccount, MoneyRequest

class TestAPIComprehensive:
    """Comprehensive API integration tests"""
    
    def test_system_health_check(self, client):
        """Test system health check endpoint"""
        response = client.get('/api/system/health')
        
        assert response.status_code in [200, 503]  # Healthy or unhealthy
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data
        assert 'checks' in data
        assert 'database' in data['checks']
    
    def test_system_ping(self, client):
        """Test system ping endpoint"""
        response = client.get('/api/system/ping')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'pong'
        assert data['status'] == 'ok'
    
    def test_api_documentation(self, client):
        """Test API documentation endpoint"""
        response = client.get('/api/system/api-docs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == 'SoftBankCashWire API Documentation'
        assert 'endpoints' in data
        assert 'authentication' in data['endpoints']
        assert 'accounts' in data['endpoints']
        assert 'transactions' in data['endpoints']
    
    def test_version_info(self, client):
        """Test version information endpoint"""
        response = client.get('/api/system/version')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['application'] == 'SoftBankCashWire'
        assert 'version' in data
        assert 'api_version' in data
    
    def test_auth_flow_complete(self, client, db_session):
        """Test complete authentication flow"""
        # Test login URL generation
        response = client.get('/api/auth/login-url')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'login_url' in data
        assert 'state' in data
        
        # Test health check for auth service
        response = client.get('/api/auth/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['service'] == 'authentication'
    
    def test_accounts_endpoints_authenticated(self, client, employee_headers, sample_users, sample_accounts):
        """Test account endpoints with authentication"""
        # Test balance endpoint
        response = client.get('/api/accounts/balance', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'balance' in data
        assert 'available_balance' in data
        assert data['currency'] == 'GBP'
        
        # Test account summary
        response = client.get('/api/accounts/summary', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'account' in data
        
        # Test account limits
        response = client.get('/api/accounts/limits', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'limits' in data
        assert 'currency' in data
        
        # Test transaction history
        response = client.get('/api/accounts/history', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'transactions' in data
        assert 'pagination' in data
        
        # Test spending analytics
        response = client.get('/api/accounts/analytics', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'period_days' in data
    
    def test_transactions_endpoints_authenticated(self, client, employee_headers, sample_users, sample_accounts):
        """Test transaction endpoints with authentication"""
        user1, user2 = sample_users[:2]
        
        # Test transaction validation
        response = client.post('/api/transactions/validate',
                             headers=employee_headers,
                             json={
                                 'recipient_id': user2.id,
                                 'amount': '50.00'
                             })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'valid' in data
        
        # Test recent transactions
        response = client.get('/api/transactions/recent', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'transactions' in data
        assert 'count' in data
        
        # Test transaction statistics
        response = client.get('/api/transactions/statistics', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'period_days' in data
        
        # Test transaction categories
        response = client.get('/api/transactions/categories', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'categories' in data
        assert len(data['categories']) > 0
    
    def test_money_requests_endpoints_authenticated(self, client, employee_headers, sample_users):
        """Test money request endpoints with authentication"""
        user1, user2 = sample_users[:2]
        
        # Test request validation
        response = client.post('/api/money-requests/validate',
                             headers=employee_headers,
                             json={
                                 'recipient_id': user2.id,
                                 'amount': '25.00'
                             })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'valid' in data
        
        # Test pending requests
        response = client.get('/api/money-requests/pending', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'requests' in data
        assert 'count' in data
        
        # Test sent requests
        response = client.get('/api/money-requests/sent', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'requests' in data
        
        # Test received requests
        response = client.get('/api/money-requests/received', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'requests' in data
        
        # Test request statistics
        response = client.get('/api/money-requests/statistics', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'period_days' in data
    
    def test_events_endpoints_authenticated(self, client, employee_headers, sample_users):
        """Test event endpoints with authentication"""
        # Test event validation
        response = client.post('/api/events/validate',
                             headers=employee_headers,
                             json={
                                 'name': 'Test Event',
                                 'description': 'Test event description',
                                 'target_amount': '200.00'
                             })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'valid' in data
        
        # Test active events
        response = client.get('/api/events/active', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'events' in data
        
        # Test my events
        response = client.get('/api/events/my-events', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'events' in data
        
        # Test my contributions
        response = client.get('/api/events/my-contributions', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'contributions' in data
        
        # Test event search
        response = client.get('/api/events/search?q=test', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'events' in data
        
        # Test event statistics
        response = client.get('/api/events/statistics', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'period_days' in data
    
    def test_reporting_endpoints_authenticated(self, client, admin_headers, employee_headers):
        """Test reporting endpoints with authentication"""
        # Test available reports (employee)
        response = client.get('/api/reporting/available', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'reports' in data
        assert len(data['reports']) == 2  # Employee should see 2 reports
        
        # Test available reports (admin)
        response = client.get('/api/reporting/available', headers=admin_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'reports' in data
        assert len(data['reports']) == 4  # Admin should see all 4 reports
        
        # Test personal analytics
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
        assert 'data' in data
        
        # Test transaction summary
        response = client.post('/api/reporting/transaction-summary',
                             headers=employee_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
    
    def test_audit_endpoints_finance_access(self, client, finance_headers):
        """Test audit endpoints with finance access"""
        # Test audit logs
        response = client.get('/api/audit/logs', headers=finance_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'audit_logs' in data
        
        # Test audit statistics
        response = client.get('/api/audit/statistics', headers=finance_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'period_days' in data
        
        # Test action types
        response = client.get('/api/audit/action-types', headers=finance_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'action_types' in data
        
        # Test audit report generation
        start_date = (datetime.now(datetime.UTC) - timedelta(days=7)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/audit/reports/generate',
                             headers=finance_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date,
                                 'report_type': 'COMPREHENSIVE'
                             })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'report_type' in data
    
    def test_system_endpoints_admin_access(self, client, admin_headers):
        """Test system endpoints with admin access"""
        # Test system info
        response = client.get('/api/system/info', headers=admin_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'application' in data
        assert 'runtime' in data
        assert 'features' in data
        
        # Test system statistics
        response = client.get('/api/system/statistics', headers=admin_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'users' in data
        assert 'accounts' in data
        assert 'transactions' in data
        assert 'events' in data
    
    def test_unauthorized_access_denied(self, client):
        """Test that unauthorized requests are properly denied"""
        # Test protected endpoints without authentication
        protected_endpoints = [
            '/api/accounts/balance',
            '/api/transactions/recent',
            '/api/money-requests/pending',
            '/api/events/active',
            '/api/reporting/available',
            '/api/system/info'
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_role_based_access_control(self, client, employee_headers, admin_headers, finance_headers):
        """Test role-based access control"""
        # Employee should not access admin endpoints
        response = client.get('/api/system/statistics', headers=employee_headers)
        assert response.status_code == 403
        
        # Employee should not access finance endpoints
        response = client.get('/api/audit/logs', headers=employee_headers)
        assert response.status_code == 403
        
        # Admin should access admin endpoints
        response = client.get('/api/system/statistics', headers=admin_headers)
        assert response.status_code == 200
        
        # Finance should access finance endpoints
        response = client.get('/api/audit/logs', headers=finance_headers)
        assert response.status_code == 200
    
    def test_input_validation_errors(self, client, employee_headers, sample_users):
        """Test input validation error handling"""
        user2 = sample_users[1]
        
        # Test invalid amount format
        response = client.post('/api/transactions/validate',
                             headers=employee_headers,
                             json={
                                 'recipient_id': user2.id,
                                 'amount': 'invalid-amount'
                             })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        
        # Test missing required fields
        response = client.post('/api/transactions/send',
                             headers=employee_headers,
                             json={
                                 'amount': '50.00'
                                 # Missing recipient_id
                             })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        
        # Test invalid JSON content type
        response = client.post('/api/transactions/send',
                             headers=employee_headers,
                             data='invalid-json',
                             content_type='text/plain')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_error_handling_consistency(self, client, employee_headers):
        """Test consistent error response format"""
        # Test 404 error
        response = client.get('/api/transactions/non-existent-id', headers=employee_headers)
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
        
        # Test validation error
        response = client.post('/api/transactions/validate',
                             headers=employee_headers,
                             json={
                                 'recipient_id': 'invalid-uuid',
                                 'amount': '50.00'
                             })
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
    
    def test_pagination_functionality(self, client, employee_headers):
        """Test pagination in list endpoints"""
        # Test transaction history pagination
        response = client.get('/api/accounts/history?page=1&per_page=10', headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'pagination' in data
        assert 'page' in data['pagination']
        assert 'per_page' in data['pagination']
        assert 'total' in data['pagination']
        
        # Test invalid pagination parameters
        response = client.get('/api/accounts/history?page=0&per_page=1000', headers=employee_headers)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_filtering_functionality(self, client, employee_headers):
        """Test filtering in list endpoints"""
        # Test transaction history filtering
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.get(f'/api/accounts/history?start_date={start_date}&end_date={end_date}',
                            headers=employee_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'transactions' in data
        
        # Test invalid date format
        response = client.get('/api/accounts/history?start_date=invalid-date',
                            headers=employee_headers)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_export_functionality(self, client, admin_headers):
        """Test export functionality in reporting"""
        start_date = (datetime.now(datetime.UTC) - timedelta(days=7)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        # Test CSV export
        response = client.post('/api/reporting/transaction-summary',
                             headers=admin_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date,
                                 'export_format': 'csv'
                             })
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv'
        
        # Test JSON export
        response = client.post('/api/reporting/transaction-summary',
                             headers=admin_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date,
                                 'export_format': 'json'
                             })
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'