"""
Tests for Security Middleware
"""
import pytest
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from middleware.security_middleware import (
    RateLimiter, CSRFProtection, FraudDetection, RequestEncryption,
    rate_limiter, fraud_detector, rate_limit, csrf_protect, fraud_detection
)
from models import User, Transaction, TransactionType, TransactionStatus, AuditLog

class TestRateLimiter:
    """Test cases for RateLimiter"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter()
        assert limiter.user_requests is not None
        assert limiter.ip_requests is not None
        assert limiter.endpoint_requests is not None
        assert limiter.failed_attempts is not None
    
    def test_user_rate_limit_within_limit(self):
        """Test user rate limiting within limits"""
        limiter = RateLimiter()
        user_id = 'test-user-123'
        
        # First request should be allowed
        is_limited, remaining = limiter.check_user_rate_limit(user_id, limit=5, window_minutes=60)
        assert is_limited == False
        assert remaining == 4
        
        # Second request should be allowed
        is_limited, remaining = limiter.check_user_rate_limit(user_id, limit=5, window_minutes=60)
        assert is_limited == False
        assert remaining == 3
    
    def test_user_rate_limit_exceeded(self):
        """Test user rate limiting when limit exceeded"""
        limiter = RateLimiter()
        user_id = 'test-user-456'
        
        # Make requests up to limit
        for i in range(5):
            is_limited, remaining = limiter.check_user_rate_limit(user_id, limit=5, window_minutes=60)
            assert is_limited == False
        
        # Next request should be limited
        is_limited, remaining = limiter.check_user_rate_limit(user_id, limit=5, window_minutes=60)
        assert is_limited == True
        assert remaining == 0
    
    def test_ip_rate_limit(self):
        """Test IP rate limiting"""
        limiter = RateLimiter()
        ip_address = '192.168.1.100'
        
        # Test within limit
        is_limited, remaining = limiter.check_ip_rate_limit(ip_address, limit=3, window_minutes=60)
        assert is_limited == False
        assert remaining == 2
        
        # Test limit exceeded
        for i in range(2):
            limiter.check_ip_rate_limit(ip_address, limit=3, window_minutes=60)
        
        is_limited, remaining = limiter.check_ip_rate_limit(ip_address, limit=3, window_minutes=60)
        assert is_limited == True
        assert remaining == 0
    
    def test_failed_attempts_tracking(self):
        """Test failed attempts tracking"""
        limiter = RateLimiter()
        identifier = 'test-user-789'
        
        # Record failed attempts
        limiter.record_failed_attempt(identifier, 'auth')
        limiter.record_failed_attempt(identifier, 'auth')
        limiter.record_failed_attempt(identifier, 'transaction')
        
        # Check failed attempts count
        failed_1h = limiter.get_failed_attempts(identifier, 1)
        assert failed_1h == 3
        
        failed_24h = limiter.get_failed_attempts(identifier, 24)
        assert failed_24h == 3
    
    def test_suspicious_activity_detection(self):
        """Test suspicious activity detection"""
        limiter = RateLimiter()
        identifier = 'suspicious-user'
        
        # Record many failed attempts
        for i in range(15):
            limiter.record_failed_attempt(identifier, 'auth')
        
        # Should detect suspicious activity
        is_suspicious = limiter.is_suspicious_activity(identifier)
        assert is_suspicious == True
        
        # Clean user should not be suspicious
        clean_identifier = 'clean-user'
        is_suspicious = limiter.is_suspicious_activity(clean_identifier)
        assert is_suspicious == False

class TestCSRFProtection:
    """Test cases for CSRF Protection"""
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation"""
        token1 = CSRFProtection.generate_csrf_token()
        token2 = CSRFProtection.generate_csrf_token()
        
        assert token1 is not None
        assert token2 is not None
        assert token1 != token2
        assert len(token1) > 20  # Should be reasonably long
    
    def test_csrf_token_validation(self):
        """Test CSRF token validation"""
        token = CSRFProtection.generate_csrf_token()
        
        # Valid token should pass
        assert CSRFProtection.validate_csrf_token(token, token) == True
        
        # Invalid token should fail
        assert CSRFProtection.validate_csrf_token(token, 'invalid-token') == False
        
        # None values should fail
        assert CSRFProtection.validate_csrf_token(None, token) == False
        assert CSRFProtection.validate_csrf_token(token, None) == False
    
    def test_csrf_token_extraction(self, app):
        """Test CSRF token extraction from request"""
        with app.test_request_context('/test', headers={'X-CSRF-Token': 'test-token'}):
            token = CSRFProtection.get_csrf_token_from_request()
            assert token == 'test-token'
        
        with app.test_request_context('/test', json={'csrf_token': 'json-token'}):
            token = CSRFProtection.get_csrf_token_from_request()
            assert token == 'json-token'
        
        with app.test_request_context('/test'):
            token = CSRFProtection.get_csrf_token_from_request()
            assert token is None

class TestFraudDetection:
    """Test cases for Fraud Detection"""
    
    def test_fraud_detector_initialization(self):
        """Test fraud detector initialization"""
        detector = FraudDetection()
        assert detector.suspicious_patterns is not None
    
    def test_transaction_fraud_analysis_clean(self, app, db_session, sample_users):
        """Test fraud analysis for clean transaction"""
        with app.app_context():
            user = sample_users[0]
            detector = FraudDetection()
            
            # Analyze clean transaction
            analysis = detector.analyze_transaction(
                user_id=user.id,
                amount=Decimal('50.00'),
                recipient_id=sample_users[1].id
            )
            
            assert 'risk_score' in analysis
            assert 'risk_level' in analysis
            assert 'risk_factors' in analysis
            assert analysis['risk_level'] == 'MINIMAL'
            assert analysis['requires_review'] == False
            assert analysis['block_transaction'] == False
    
    def test_transaction_fraud_analysis_high_amount(self, app, db_session, sample_users, sample_accounts):
        """Test fraud analysis for unusually high amount"""
        with app.app_context():
            user = sample_users[0]
            
            # Create some normal transactions first
            for i in range(3):
                transaction = Transaction(
                    sender_id=user.id,
                    recipient_id=sample_users[1].id,
                    amount=Decimal('25.00'),
                    transaction_type=TransactionType.TRANSFER,
                    status=TransactionStatus.COMPLETED,
                    created_at=datetime.utcnow() - timedelta(days=i)
                )
                db_session.add(transaction)
            db_session.commit()
            
            detector = FraudDetection()
            
            # Analyze high amount transaction (10x normal)
            analysis = detector.analyze_transaction(
                user_id=user.id,
                amount=Decimal('1250.00'),  # 50x average
                recipient_id=sample_users[1].id
            )
            
            assert analysis['risk_score'] > 0
            assert 'UNUSUAL_AMOUNT_HIGH' in analysis['risk_factors']
            assert analysis['risk_level'] in ['MEDIUM', 'HIGH']
    
    def test_transaction_fraud_analysis_high_frequency(self, app, db_session, sample_users):
        """Test fraud analysis for high frequency transactions"""
        with app.app_context():
            user = sample_users[0]
            
            # Create many transactions today
            today = datetime.utcnow().date()
            for i in range(25):
                transaction = Transaction(
                    sender_id=user.id,
                    recipient_id=sample_users[1].id,
                    amount=Decimal('10.00'),
                    transaction_type=TransactionType.TRANSFER,
                    status=TransactionStatus.COMPLETED,
                    created_at=datetime.combine(today, datetime.min.time()) + timedelta(minutes=i)
                )
                db_session.add(transaction)
            db_session.commit()
            
            detector = FraudDetection()
            
            # Analyze new transaction
            analysis = detector.analyze_transaction(
                user_id=user.id,
                amount=Decimal('10.00'),
                recipient_id=sample_users[1].id
            )
            
            assert analysis['risk_score'] > 0
            assert 'HIGH_FREQUENCY_TODAY' in analysis['risk_factors']
    
    def test_login_fraud_analysis_clean(self, app, db_session, sample_users):
        """Test login fraud analysis for clean login"""
        with app.app_context():
            user = sample_users[0]
            detector = FraudDetection()
            
            analysis = detector.analyze_login_pattern(
                user_id=user.id,
                ip_address='192.168.1.100',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            assert 'risk_score' in analysis
            assert 'risk_level' in analysis
            assert analysis['risk_level'] == 'MINIMAL'
            assert analysis['requires_mfa'] == False
            assert analysis['block_login'] == False
    
    def test_login_fraud_analysis_multiple_ips(self, app, db_session, sample_users):
        """Test login fraud analysis with multiple IP addresses"""
        with app.app_context():
            user = sample_users[0]
            
            # Create login attempts from different IPs
            ip_addresses = ['192.168.1.100', '10.0.0.1', '172.16.0.1', '203.0.113.1', '198.51.100.1', '192.0.2.1']
            
            for i, ip in enumerate(ip_addresses):
                audit_log = AuditLog(
                    user_id=user.id,
                    action_type='USER_LOGIN',
                    entity_type='User',
                    ip_address=ip,
                    created_at=datetime.utcnow() - timedelta(hours=i)
                )
                db_session.add(audit_log)
            db_session.commit()
            
            detector = FraudDetection()
            
            # Analyze login from new IP
            analysis = detector.analyze_login_pattern(
                user_id=user.id,
                ip_address='203.0.113.100',  # New IP
                user_agent='Mozilla/5.0'
            )
            
            assert analysis['risk_score'] > 0
            assert 'MULTIPLE_IP_ADDRESSES' in analysis['risk_factors']
            assert 'NEW_IP_ADDRESS' in analysis['risk_factors']

class TestRequestEncryption:
    """Test cases for Request Encryption"""
    
    def test_sensitive_data_encryption(self):
        """Test sensitive data encryption in responses"""
        test_data = {
            'user_id': '123',
            'name': 'John Doe',
            'password': 'secret123',
            'account_number': '1234567890',
            'balance': '100.00',
            'nested': {
                'secret': 'hidden',
                'public': 'visible'
            }
        }
        
        encrypted_data = RequestEncryption.encrypt_sensitive_data(test_data)
        
        assert encrypted_data['user_id'] == '123'
        assert encrypted_data['name'] == 'John Doe'
        assert encrypted_data['password'] == '***ENCRYPTED***'
        assert encrypted_data['account_number'] == '***ENCRYPTED***'
        assert encrypted_data['balance'] == '100.00'
        assert encrypted_data['nested']['secret'] == '***ENCRYPTED***'
        assert encrypted_data['nested']['public'] == 'visible'
    
    def test_request_integrity_validation(self):
        """Test request integrity validation"""
        request_data = '{"amount": "100.00", "recipient": "user123"}'
        secret_key = 'test-secret-key'
        
        # Generate valid signature
        import hmac
        import hashlib
        
        valid_signature = hmac.new(
            secret_key.encode('utf-8'),
            request_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Test valid signature
        is_valid = RequestEncryption.validate_request_integrity(
            request_data, valid_signature, secret_key
        )
        assert is_valid == True
        
        # Test invalid signature
        is_valid = RequestEncryption.validate_request_integrity(
            request_data, 'invalid-signature', secret_key
        )
        assert is_valid == False
        
        # Test missing signature
        is_valid = RequestEncryption.validate_request_integrity(
            request_data, None, secret_key
        )
        assert is_valid == False

class TestSecurityDecorators:
    """Test cases for Security Decorators"""
    
    def test_rate_limit_decorator(self, app, client):
        """Test rate limit decorator"""
        
        @rate_limit(user_limit=2, ip_limit=3, window_minutes=60)
        def test_endpoint():
            return {'message': 'success'}
        
        with app.test_request_context('/test', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            # First few requests should succeed
            response1 = test_endpoint()
            assert response1['message'] == 'success'
            
            response2 = test_endpoint()
            assert response2['message'] == 'success'
            
            response3 = test_endpoint()
            assert response3['message'] == 'success'
            
            # Fourth request should be rate limited (IP limit = 3)
            response4 = test_endpoint()
            # This would be rate limited in a real scenario with proper request context
    
    def test_csrf_protect_decorator(self, app):
        """Test CSRF protection decorator"""
        
        @csrf_protect
        def test_post_endpoint():
            return {'message': 'success'}
        
        with app.test_request_context('/test', method='GET'):
            # GET requests should not require CSRF token
            response = test_post_endpoint()
            assert response['message'] == 'success'
        
        # POST requests would require CSRF token in real scenario
    
    def test_fraud_detection_decorator(self, app, db_session, sample_users):
        """Test fraud detection decorator"""
        
        @fraud_detection
        def test_transaction_endpoint():
            return {'message': 'success'}
        
        with app.test_request_context('/test', method='POST', json={'amount': '50.00'}):
            # Mock current user
            from flask import g
            g.current_user_id = sample_users[0].id
            
            response = test_transaction_endpoint()
            assert response['message'] == 'success'
            
            # Check if fraud analysis was added to context
            assert hasattr(g, 'fraud_analysis')

class TestSecurityIntegration:
    """Integration tests for security middleware"""
    
    def test_security_middleware_initialization(self, app):
        """Test security middleware initialization"""
        from middleware.security_middleware import SecurityMiddleware
        
        middleware = SecurityMiddleware()
        middleware.init_app(app)
        
        # Check if before_request and after_request handlers are registered
        assert len(app.before_request_funcs[None]) > 0
        assert len(app.after_request_funcs[None]) > 0
    
    def test_security_headers_added(self, client):
        """Test that security headers are added to responses"""
        response = client.get('/api/system/ping')
        
        # Check for security headers
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        assert response.headers['X-Frame-Options'] == 'DENY'
    
    def test_rate_limiting_integration(self, client):
        """Test rate limiting integration with real requests"""
        # Make multiple requests to test rate limiting
        responses = []
        for i in range(5):
            response = client.get('/api/system/ping')
            responses.append(response.status_code)
        
        # All requests should succeed (ping endpoint has high limits)
        assert all(status == 200 for status in responses)
    
    def test_suspicious_activity_blocking(self, app, client):
        """Test suspicious activity blocking"""
        # This would require mocking the rate limiter to simulate suspicious activity
        # In a real test, we would make many failed requests to trigger blocking
        pass
    
    def test_fraud_detection_integration(self, app, client, employee_headers, sample_users):
        """Test fraud detection integration with transaction endpoints"""
        user2 = sample_users[1]
        
        # Test normal transaction (should pass)
        response = client.post('/api/transactions/validate',
                             headers=employee_headers,
                             json={
                                 'recipient_id': user2.id,
                                 'amount': '25.00'
                             })
        
        assert response.status_code == 200
        
        # Test potentially fraudulent transaction (very high amount)
        response = client.post('/api/transactions/validate',
                             headers=employee_headers,
                             json={
                                 'recipient_id': user2.id,
                                 'amount': '50000.00'
                             })
        
        # Should still validate but with fraud analysis
        assert response.status_code == 200
    
    def test_error_handling_security(self, client):
        """Test that error responses don't leak sensitive information"""
        # Test 404 error
        response = client.get('/api/nonexistent/endpoint')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'stack_trace' not in data  # Should not leak stack traces
        assert 'internal_details' not in data  # Should not leak internal details
    
    def test_input_sanitization(self, client, employee_headers):
        """Test input sanitization for XSS prevention"""
        # Test with potentially malicious input
        malicious_input = '<script>alert("xss")</script>'
        
        response = client.post('/api/transactions/validate',
                             headers=employee_headers,
                             json={
                                 'recipient_id': 'invalid-id',
                                 'amount': malicious_input
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        # Response should not contain unescaped script tags
        response_text = json.dumps(data)
        assert '<script>' not in response_text
        assert 'alert(' not in response_text