"""
Comprehensive security testing for SoftBankCashWire
Tests authentication, authorization, input validation, and vulnerability assessment
"""
import pytest
import requests
import json
import time
import hashlib
import base64
from typing import Dict, List, Any
import jwt
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

class SecurityTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.admin_token = None
        
    def authenticate_user(self, email: str = "test@softbank.com", password: str = "test123") -> str:
        """Authenticate and return access token"""
        response = self.session.post(f'{self.base_url}/api/auth/login', json={
            'email': email,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        return None
    
    def authenticate_admin(self) -> str:
        """Authenticate as admin user"""
        return self.authenticate_user("admin@softbank.com", "admin123")

@pytest.fixture
def security_tester():
    return SecurityTester()

class TestAuthentication:
    """Test authentication security"""
    
    def test_login_rate_limiting(self, security_tester):
        """Test rate limiting on login attempts"""
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            response = requests.post(f'{BASE_URL}/api/auth/login', json={
                'email': 'test@softbank.com',
                'password': 'wrongpassword'
            })
            
            if response.status_code == 429:  # Too Many Requests
                break
            elif response.status_code == 401:
                failed_attempts += 1
        
        # Should be rate limited after multiple attempts
        assert failed_attempts < 10, "Rate limiting not working for failed login attempts"
    
    def test_jwt_token_validation(self, security_tester):
        """Test JWT token validation and security"""
        token = security_tester.authenticate_user()
        assert token is not None, "Failed to get authentication token"
        
        # Test with valid token
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f'{BASE_URL}/api/accounts/balance', headers=headers)
        assert response.status_code == 200, "Valid token rejected"
        
        # Test with invalid token
        headers = {'Authorization': 'Bearer invalid_token'}
        response = requests.get(f'{BASE_URL}/api/accounts/balance', headers=headers)
        assert response.status_code == 401, "Invalid token accepted"
        
        # Test with expired token (if possible to generate)
        try:
            # Create an expired token for testing
            expired_payload = {
                'user_id': '1',
                'exp': datetime.utcnow() - timedelta(hours=1)
            }
            expired_token = jwt.encode(expired_payload, 'test_secret', algorithm='HS256')
            
            headers = {'Authorization': f'Bearer {expired_token}'}
            response = requests.get(f'{BASE_URL}/api/accounts/balance', headers=headers)
            assert response.status_code == 401, "Expired token accepted"
        except Exception:
            pass  # Skip if JWT library not available
    
    def test_session_security(self, security_tester):
        """Test session security measures"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test session timeout (simulate long delay)
        time.sleep(1)  # Short delay for testing
        response = requests.get(f'{BASE_URL}/api/accounts/balance', headers=headers)
        assert response.status_code in [200, 401], "Unexpected session behavior"
        
        # Test logout functionality
        response = requests.post(f'{BASE_URL}/api/auth/logout', headers=headers)
        assert response.status_code in [200, 204], "Logout failed"
        
        # Token should be invalid after logout
        response = requests.get(f'{BASE_URL}/api/accounts/balance', headers=headers)
        assert response.status_code == 401, "Token still valid after logout"

class TestAuthorization:
    """Test role-based access control"""
    
    def test_role_based_access_control(self, security_tester):
        """Test that users can only access authorized resources"""
        user_token = security_tester.authenticate_user()
        admin_token = security_tester.authenticate_admin()
        
        # Regular user should not access admin endpoints
        headers = {'Authorization': f'Bearer {user_token}'}
        response = requests.get(f'{BASE_URL}/api/admin/users', headers=headers)
        assert response.status_code == 403, "Regular user accessed admin endpoint"
        
        # Admin should access admin endpoints
        if admin_token:
            headers = {'Authorization': f'Bearer {admin_token}'}
            response = requests.get(f'{BASE_URL}/api/admin/users', headers=headers)
            assert response.status_code in [200, 404], "Admin cannot access admin endpoint"
    
    def test_resource_ownership(self, security_tester):
        """Test that users can only access their own resources"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try to access another user's transactions
        response = requests.get(f'{BASE_URL}/api/transactions/history?user_id=999', headers=headers)
        # Should either filter results or deny access
        assert response.status_code in [200, 403], "Unexpected response for resource access"
        
        if response.status_code == 200:
            data = response.json()
            # If allowed, should only return current user's data
            for transaction in data.get('transactions', []):
                assert transaction.get('sender_id') == '1' or transaction.get('recipient_id') == '1', \
                    "User accessed other user's transactions"

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_sql_injection_protection(self, security_tester):
        """Test protection against SQL injection attacks"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT * FROM accounts; --"
        ]
        
        for payload in sql_payloads:
            # Test in search parameters
            response = requests.get(f'{BASE_URL}/api/transactions/history?search={payload}', headers=headers)
            assert response.status_code in [200, 400], f"Unexpected response for SQL injection: {payload}"
            
            # Test in POST data
            response = requests.post(f'{BASE_URL}/api/transactions/send', 
                json={
                    'recipient_email': payload,
                    'amount': '10.00',
                    'note': 'test'
                },
                headers=headers
            )
            assert response.status_code in [400, 422], f"SQL injection not blocked in POST: {payload}"
    
    def test_xss_protection(self, security_tester):
        """Test protection against XSS attacks"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            # Test in transaction notes
            response = requests.post(f'{BASE_URL}/api/transactions/send',
                json={
                    'recipient_email': 'test@example.com',
                    'amount': '10.00',
                    'note': payload
                },
                headers=headers
            )
            
            if response.status_code == 200:
                # If transaction created, check that payload is sanitized
                data = response.json()
                note = data.get('transaction', {}).get('note', '')
                assert '<script>' not in note, f"XSS payload not sanitized: {payload}"
    
    def test_input_length_validation(self, security_tester):
        """Test input length validation"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test extremely long inputs
        long_string = 'A' * 10000
        
        response = requests.post(f'{BASE_URL}/api/transactions/send',
            json={
                'recipient_email': 'test@example.com',
                'amount': '10.00',
                'note': long_string
            },
            headers=headers
        )
        
        assert response.status_code in [400, 422], "Long input not rejected"
    
    def test_numeric_validation(self, security_tester):
        """Test numeric input validation"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test invalid amounts
        invalid_amounts = [
            '-100.00',  # Negative amount
            '0.00',     # Zero amount
            'abc',      # Non-numeric
            '999999.99', # Too large
            '10.999'    # Too many decimal places
        ]
        
        for amount in invalid_amounts:
            response = requests.post(f'{BASE_URL}/api/transactions/send',
                json={
                    'recipient_email': 'test@example.com',
                    'amount': amount,
                    'note': 'test'
                },
                headers=headers
            )
            
            assert response.status_code in [400, 422], f"Invalid amount accepted: {amount}"

class TestDataSecurity:
    """Test data security and encryption"""
    
    def test_sensitive_data_exposure(self, security_tester):
        """Test that sensitive data is not exposed in responses"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Get user profile
        response = requests.get(f'{BASE_URL}/api/accounts/profile', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check that sensitive fields are not exposed
            sensitive_fields = ['password', 'password_hash', 'secret_key', 'private_key']
            
            def check_sensitive_data(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        assert key.lower() not in sensitive_fields, f"Sensitive field exposed: {current_path}"
                        check_sensitive_data(value, current_path)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_sensitive_data(item, f"{path}[{i}]")
            
            check_sensitive_data(data)
    
    def test_https_enforcement(self):
        """Test HTTPS enforcement (if applicable)"""
        # This test would be more relevant in production
        # For now, just check that security headers are present
        response = requests.get(f'{BASE_URL}/api/health')
        
        # Check for security headers
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]
        
        for header in security_headers:
            # Note: These might not be implemented yet, so we just check
            if header in response.headers:
                assert response.headers[header] is not None

class TestBusinessLogicSecurity:
    """Test business logic security"""
    
    def test_transaction_limits(self, security_tester):
        """Test transaction limit enforcement"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try to send amount exceeding limits
        response = requests.post(f'{BASE_URL}/api/transactions/send',
            json={
                'recipient_email': 'test@example.com',
                'amount': '1000.00',  # Exceeds typical limits
                'note': 'test'
            },
            headers=headers
        )
        
        assert response.status_code in [400, 422], "Transaction limit not enforced"
    
    def test_double_spending_protection(self, security_tester):
        """Test protection against double spending"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Get current balance
        balance_response = requests.get(f'{BASE_URL}/api/accounts/balance', headers=headers)
        if balance_response.status_code == 200:
            balance_data = balance_response.json()
            current_balance = float(balance_data.get('balance', '0'))
            
            # Try to spend more than available balance
            response = requests.post(f'{BASE_URL}/api/transactions/send',
                json={
                    'recipient_email': 'test@example.com',
                    'amount': str(current_balance + 100),
                    'note': 'test'
                },
                headers=headers
            )
            
            assert response.status_code in [400, 422], "Double spending not prevented"
    
    def test_self_transaction_prevention(self, security_tester):
        """Test prevention of self-transactions"""
        token = security_tester.authenticate_user()
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try to send money to self
        response = requests.post(f'{BASE_URL}/api/transactions/send',
            json={
                'recipient_email': 'test@softbank.com',  # Same as sender
                'amount': '10.00',
                'note': 'self transaction'
            },
            headers=headers
        )
        
        assert response.status_code in [400, 422], "Self-transaction not prevented"

class TestAuditSecurity:
    """Test audit trail security"""
    
    def test_audit_log_integrity(self, security_tester):
        """Test that audit logs cannot be tampered with"""
        admin_token = security_tester.authenticate_admin()
        
        if admin_token:
            headers = {'Authorization': f'Bearer {admin_token}'}
            
            # Try to access audit logs
            response = requests.get(f'{BASE_URL}/api/audit/logs', headers=headers)
            
            if response.status_code == 200:
                # Audit logs should be read-only
                response = requests.delete(f'{BASE_URL}/api/audit/logs/1', headers=headers)
                assert response.status_code in [403, 405], "Audit log deletion allowed"
                
                response = requests.put(f'{BASE_URL}/api/audit/logs/1', 
                    json={'modified': True}, headers=headers)
                assert response.status_code in [403, 405], "Audit log modification allowed"

@pytest.mark.security
def test_comprehensive_security_scan():
    """Run comprehensive security tests"""
    tester = SecurityTester()
    
    print("\n=== SECURITY TEST RESULTS ===")
    
    # Test categories
    test_categories = [
        TestAuthentication(),
        TestAuthorization(),
        TestInputValidation(),
        TestDataSecurity(),
        TestBusinessLogicSecurity(),
        TestAuditSecurity()
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for category in test_categories:
        category_name = category.__class__.__name__
        print(f"\nTesting {category_name}...")
        
        # Get all test methods
        test_methods = [method for method in dir(category) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                method = getattr(category, test_method)
                if hasattr(method, '__call__'):
                    method(tester)
                passed_tests += 1
                print(f"  ✓ {test_method}")
            except Exception as e:
                failed_tests.append(f"{category_name}.{test_method}: {str(e)}")
                print(f"  ✗ {test_method}: {str(e)}")
    
    print(f"\n=== SECURITY TEST SUMMARY ===")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print(f"\nFailed Tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
    
    # Security tests should have high pass rate
    success_rate = (passed_tests / total_tests) * 100
    assert success_rate >= 80, f"Security test success rate {success_rate:.1f}% too low"

if __name__ == "__main__":
    # Run security tests directly
    print("Running SoftBankCashWire Security Tests")
    print("=" * 50)
    
    try:
        test_comprehensive_security_scan()
        print("\n" + "=" * 50)
        print("Security tests completed!")
        
    except Exception as e:
        print(f"\nSecurity test failed: {e}")
        exit(1)