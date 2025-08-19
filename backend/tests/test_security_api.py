"""
Tests for Security API endpoints
"""
import pytest
import json
from datetime import datetime, timedelta
from models import User, AuditLog

class TestSecurityAPI:
    """Test cases for Security API endpoints"""
    
    def test_security_health_check(self, client):
        """Test security service health check"""
        response = client.get('/api/security/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['service'] == 'security'
        assert data['status'] == 'healthy'
        assert 'features' in data
        assert data['features']['threat_monitoring'] == True
        assert data['features']['fraud_detection'] == True
    
    def test_monitor_threats_admin_access(self, client, admin_headers):
        """Test threat monitoring with admin access"""
        response = client.get('/api/security/threats/monitor', headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        assert 'threat_level' in data['data']
        assert 'active_threats' in data['data']
        assert 'critical_alerts' in data['data']
        assert 'monitoring_status' in data['data']
    
    def test_monitor_threats_employee_denied(self, client, employee_headers):
        """Test threat monitoring denied for employee"""
        response = client.get('/api/security/threats/monitor', headers=employee_headers)
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Admin access required' in data['error']
    
    def test_analyze_security_events_finance_access(self, client, finance_headers):
        """Test security event analysis with finance access"""
        start_date = (datetime.now(datetime.UTC) - timedelta(days=7)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/security/analysis/events',
                             headers=finance_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        assert 'period' in data['data']
        assert 'summary' in data['data']
        assert 'event_breakdown' in data['data']
        assert 'threat_indicators' in data['data']
    
    def test_analyze_security_events_invalid_dates(self, client, finance_headers):
        """Test security event analysis with invalid dates"""
        # Test with start_date after end_date
        start_date = datetime.now(datetime.UTC).isoformat()
        end_date = (datetime.now(datetime.UTC) - timedelta(days=1)).isoformat()
        
        response = client.post('/api/security/analysis/events',
                             headers=finance_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'start_date must be before end_date' in data['error']
    
    def test_analyze_security_events_date_range_too_large(self, client, finance_headers):
        """Test security event analysis with date range too large"""
        end_date = datetime.now(datetime.UTC)
        start_date = end_date - timedelta(days=100)  # More than 90 days
        
        response = client.post('/api/security/analysis/events',
                             headers=finance_headers,
                             json={
                                 'start_date': start_date.isoformat(),
                                 'end_date': end_date.isoformat()
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Date range cannot exceed 90 days' in data['error']
    
    def test_analyze_user_behavior_finance_access(self, client, finance_headers, sample_users):
        """Test user behavior analysis with finance access"""
        user = sample_users[0]
        
        response = client.get(f'/api/security/analysis/user/{user.id}?days=7',
                            headers=finance_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        assert data['data']['user_id'] == user.id
        assert 'behavioral_anomalies' in data['data']
        assert 'risk_score' in data['data']
        assert 'risk_level' in data['data']
    
    def test_analyze_user_behavior_invalid_days(self, client, finance_headers, sample_users):
        """Test user behavior analysis with invalid days parameter"""
        user = sample_users[0]
        
        response = client.get(f'/api/security/analysis/user/{user.id}?days=50',
                            headers=finance_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Days must be between 1 and 30' in data['error']
    
    def test_generate_compliance_report_admin_access(self, client, admin_headers):
        """Test compliance report generation with admin access"""
        start_date = (datetime.now(datetime.UTC) - timedelta(days=30)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/security/compliance/report',
                             headers=admin_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        assert data['data']['report_type'] == 'SECURITY_COMPLIANCE'
        assert 'compliance_metrics' in data['data']
        assert 'compliance_score' in data['data']
        assert 'recommendations' in data['data']
    
    def test_get_security_status_admin_access(self, client, admin_headers):
        """Test security status with admin access"""
        response = client.get('/api/security/status', headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        assert 'overall_status' in data['data']
        assert 'threat_level' in data['data']
        assert 'active_threats' in data['data']
        assert 'security_metrics' in data['data']
        assert 'recommendations' in data['data']
    
    def test_get_security_alerts_admin_access(self, client, admin_headers):
        """Test security alerts with admin access"""
        response = client.get('/api/security/alerts', headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        assert 'alerts' in data['data']
        assert 'total_count' in data['data']
        assert 'active_count' in data['data']
        assert 'critical_count' in data['data']
    
    def test_get_security_alerts_with_filters(self, client, admin_headers):
        """Test security alerts with filters"""
        response = client.get('/api/security/alerts?severity=CRITICAL&limit=10',
                            headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['data']['alerts']) <= 10
    
    def test_get_security_alerts_invalid_limit(self, client, admin_headers):
        """Test security alerts with invalid limit"""
        response = client.get('/api/security/alerts?limit=500',
                            headers=admin_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Limit must be between 1 and 200' in data['error']
    
    def test_get_security_config_admin_access(self, client, admin_headers):
        """Test security configuration with admin access"""
        response = client.get('/api/security/config', headers=admin_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data
        assert 'environment' in data['data']
        assert 'rate_limiting' in data['data']
        assert 'csrf_protection' in data['data']
        assert 'fraud_detection' in data['data']
        assert 'security_headers' in data['data']
    
    def test_unauthorized_access_denied(self, client):
        """Test that unauthorized requests are denied"""
        protected_endpoints = [
            '/api/security/threats/monitor',
            '/api/security/status',
            '/api/security/alerts',
            '/api/security/config'
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401
            data = json.loads(response.data)
            assert data['success'] == False
    
    def test_employee_access_denied(self, client, employee_headers):
        """Test that employee access is denied for admin endpoints"""
        admin_endpoints = [
            '/api/security/threats/monitor',
            '/api/security/status',
            '/api/security/alerts',
            '/api/security/config'
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=employee_headers)
            assert response.status_code == 403
            data = json.loads(response.data)
            assert data['success'] == False
    
    def test_finance_access_to_analysis_endpoints(self, client, finance_headers, sample_users):
        """Test that finance team can access analysis endpoints"""
        user = sample_users[0]
        
        # Test event analysis
        start_date = (datetime.now(datetime.UTC) - timedelta(days=7)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/security/analysis/events',
                             headers=finance_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        assert response.status_code == 200
        
        # Test user behavior analysis
        response = client.get(f'/api/security/analysis/user/{user.id}',
                            headers=finance_headers)
        assert response.status_code == 200
    
    def test_missing_request_body_validation(self, client, finance_headers):
        """Test validation for missing request body"""
        response = client.post('/api/security/analysis/events',
                             headers=finance_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Request body is required' in data['error']
    
    def test_invalid_date_format_validation(self, client, finance_headers):
        """Test validation for invalid date format"""
        response = client.post('/api/security/analysis/events',
                             headers=finance_headers,
                             json={
                                 'start_date': 'invalid-date',
                                 'end_date': datetime.now(datetime.UTC).isoformat()
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'start_date and end_date are required in ISO format' in data['error']
    
    def test_rate_limiting_headers(self, client, admin_headers):
        """Test that rate limiting is applied to security endpoints"""
        # Make multiple requests to test rate limiting
        responses = []
        for i in range(3):
            response = client.get('/api/security/status', headers=admin_headers)
            responses.append(response.status_code)
        
        # All requests should succeed (within rate limits for testing)
        assert all(status == 200 for status in responses)
    
    def test_security_headers_present(self, client):
        """Test that security headers are present in responses"""
        response = client.get('/api/security/health')
        
        # Check for security headers
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['X-Frame-Options'] == 'DENY'
    
    def test_error_handling_consistency(self, client, admin_headers):
        """Test consistent error response format"""
        # Test 400 error
        response = client.post('/api/security/analysis/events',
                             headers=admin_headers,
                             json={'invalid': 'data'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'success' in data
        assert data['success'] == False
        assert 'error' in data
    
    def test_compliance_report_validation(self, client, admin_headers):
        """Test compliance report parameter validation"""
        # Test missing dates
        response = client.post('/api/security/compliance/report',
                             headers=admin_headers,
                             json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'start_date and end_date are required' in data['error']
    
    def test_security_event_analysis_with_data(self, client, finance_headers, db_session, sample_users):
        """Test security event analysis with actual audit data"""
        # Create some test audit logs
        user = sample_users[0]
        
        # Create security-related audit logs
        security_log1 = AuditLog(
            user_id=user.id,
            action_type='LOGIN_FAILED',
            entity_type='User',
            ip_address='192.168.1.100',
            created_at=datetime.now(datetime.UTC) - timedelta(hours=2)
        )
        
        security_log2 = AuditLog(
            user_id=user.id,
            action_type='RATE_LIMIT_EXCEEDED',
            entity_type='SecurityEvent',
            ip_address='192.168.1.100',
            created_at=datetime.now(datetime.UTC) - timedelta(hours=1)
        )
        
        db_session.add_all([security_log1, security_log2])
        db_session.commit()
        
        # Analyze security events
        start_date = (datetime.now(datetime.UTC) - timedelta(days=1)).isoformat()
        end_date = datetime.now(datetime.UTC).isoformat()
        
        response = client.post('/api/security/analysis/events',
                             headers=finance_headers,
                             json={
                                 'start_date': start_date,
                                 'end_date': end_date
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        
        # Should have detected the security events
        assert data['data']['summary']['total_security_events'] >= 2
        assert data['data']['summary']['unique_users_affected'] >= 1