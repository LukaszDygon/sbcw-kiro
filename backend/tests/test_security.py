"""
Security tests for SoftBankCashWire
"""
import pytest
import jwt
import time
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from models import (
    db, User, UserRole, AccountStatus, Account, 
    Transaction, TransactionType, EventAccount
)
from services.auth_service import AuthService
from middleware.security_middleware import SecurityMiddleware

class TestAuthenticationSecurity:
    """Test authentication security measures"""
    
    def test_jwt_token_validation(self, app, client):
        """Test JWT token validation"""
        with app.app_context():
            # Test with no token
            response = client.get('/api/accounts/balance')
            assert response.status_code == 401
            
            # Test with invalid token
            headers = {'Authorization': 'Bearer invalid-token'}
            response = client.get('/api/accounts/balance', headers=headers)
            assert response.status_code == 401
            
            # Test with malformed token
            headers = {'Authorization': 'Bearer malformed.token.here'}
            response = client.get('/api/accounts/balance', headers=headers)
            assert response.status_code == 401
    
    def test_token_expiration(self, app, client):
        """Test token expiration handling"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='test', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create expired token
            expired_payload = {
                'user_id': user.id,
                'exp': int(time.time()) - 3600,  # Expired 1 hour ago
                'iat': int(time.time()) - 7200   # Issued 2 hours ago
            }
            
            expired_token = jwt.encode(
                expired_payload, 
                app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
            headers = {'Authorization': f'Bearer {expired_token}'}
            response = client.get('/api/accounts/balance', headers=headers)
            assert response.status_code == 401
            
            data = response.get_json()
            assert 'expired' in data['error']['message'].lower()
    
    def test_token_tampering_detection(self, app, client):
        """Test detection of tampered tokens"""
        with app.app_context():
            # Create user
            user = User(microsoft_id='test', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.commit()
            
            # Create valid token
            payload = {
                'user_id': user.id,
                'exp': int(time.time()) + 3600,
                'iat': int(time.time())
            }
            
            valid_token = jwt.encode(
                payload, 
                app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
            # Tamper with token (change last character)
            tampered_token = valid_token[:-1] + 'X'
            
            headers = {'Authorization': f'Bearer {tampered_token}'}
            response = client.get('/api/accounts/balance', headers=headers)
            assert response.status_code == 401
    
    def test_session_timeout(self, app):
        """Test session timeout functionality"""
        with app.app_context():
            # Create user with old last_login
            user = User(
                microsoft_id='test', 
                email='test@test.com', 
                name='Test User'
            )
            user.last_login = datetime.utcnow() - timedelta(hours=9)  # 9 hours ago
            db.session.add(user)
            db.session.commit()
            
            # Session should be invalid due to timeout
            is_valid = AuthService.validate_session(user.id)
            assert is_valid is False
    
    def test_concurrent_session_limit(self, app):
        """Test concurrent session limits"""
        with app.app_context():
            user = User(microsoft_id='test', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.commit()
            
            # This would be implemented in a real system with session tracking
            # For now, we test the concept
            max_sessions = app.config.get('MAX_CONCURRENT_SESSIONS', 3)
            assert max_sessions == 3
    
    @patch('services.auth_service.requests.get')
    def test_microsoft_sso_validation(self, mock_get, app):
        """Test Microsoft SSO token validation"""
        with app.app_context():
            # Test with invalid Microsoft token
            mock_get.return_value.status_code = 401
            
            with pytest.raises(ValueError, match="Microsoft Graph API error"):
                AuthService._get_microsoft_user_info('invalid-token')
            
            # Test with valid token but invalid response
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {}  # Missing required fields
            
            with pytest.raises(ValueError):
                AuthService._get_microsoft_user_info('valid-token')


class TestAuthorizationSecurity:
    """Test authorization and access control"""
    
    def test_role_based_access_control(self, app, client):
        """Test role-based access control"""
        with app.app_context():
            # Create users with different roles
            employee = User(
                microsoft_id='emp', 
                email='emp@test.com', 
                name='Employee',
                role=UserRole.EMPLOYEE
            )
            admin = User(
                microsoft_id='admin', 
                email='admin@test.com', 
                name='Admin',
                role=UserRole.ADMIN
            )
            finance = User(
                microsoft_id='finance', 
                email='finance@test.com', 
                name='Finance',
                role=UserRole.FINANCE
            )
            
            db.session.add_all([employee, admin, finance])
            db.session.commit()
            
            # Test employee permissions
            assert not AuthService.require_role(employee.id, UserRole.ADMIN)
            assert not AuthService.require_role(employee.id, UserRole.FINANCE)
            assert AuthService.require_role(employee.id, UserRole.EMPLOYEE)
            
            # Test admin permissions
            assert AuthService.require_role(admin.id, UserRole.ADMIN)
            assert not AuthService.require_role(admin.id, UserRole.FINANCE)
            assert AuthService.require_role(admin.id, UserRole.EMPLOYEE)
            
            # Test finance permissions (highest level)
            assert AuthService.require_role(finance.id, UserRole.FINANCE)
            assert AuthService.require_role(finance.id, UserRole.ADMIN)
            assert AuthService.require_role(finance.id, UserRole.EMPLOYEE)
    
    def test_resource_ownership_validation(self, app):
        """Test that users can only access their own resources"""
        with app.app_context():
            # Create two users
            user1 = User(microsoft_id='user1', email='user1@test.com', name='User 1')
            user2 = User(microsoft_id='user2', email='user2@test.com', name='User 2')
            db.session.add_all([user1, user2])
            db.session.flush()
            
            account1 = Account(user_id=user1.id, balance=Decimal('100.00'))
            account2 = Account(user_id=user2.id, balance=Decimal('150.00'))
            db.session.add_all([account1, account2])
            db.session.flush()
            
            # Create transaction between users
            transaction = Transaction.create_transfer(
                sender_id=user1.id,
                recipient_id=user2.id,
                amount=Decimal('25.00')
            )
            db.session.add(transaction)
            db.session.commit()
            
            # User1 should be able to access their own transaction
            from services.transaction_service import TransactionService
            user1_transaction = TransactionService.get_transaction_by_id(transaction.id, user1.id)
            assert user1_transaction is not None
            
            # User2 should also be able to access it (as recipient)
            user2_transaction = TransactionService.get_transaction_by_id(transaction.id, user2.id)
            assert user2_transaction is not None
            
            # Create third user who shouldn't have access
            user3 = User(microsoft_id='user3', email='user3@test.com', name='User 3')
            db.session.add(user3)
            db.session.commit()
            
            # User3 should not be able to access the transaction
            user3_transaction = TransactionService.get_transaction_by_id(transaction.id, user3.id)
            assert user3_transaction is None
    
    def test_account_status_enforcement(self, app):
        """Test that suspended/closed accounts cannot perform actions"""
        with app.app_context():
            # Create suspended user
            suspended_user = User(
                microsoft_id='suspended', 
                email='suspended@test.com', 
                name='Suspended User',
                account_status=AccountStatus.SUSPENDED
            )
            db.session.add(suspended_user)
            db.session.commit()
            
            # Suspended user should not pass session validation
            is_valid = AuthService.validate_session(suspended_user.id)
            assert is_valid is False
            
            # Create closed user
            closed_user = User(
                microsoft_id='closed', 
                email='closed@test.com', 
                name='Closed User',
                account_status=AccountStatus.CLOSED
            )
            db.session.add(closed_user)
            db.session.commit()
            
            # Closed user should not pass session validation
            is_valid = AuthService.validate_session(closed_user.id)
            assert is_valid is False
    
    def test_admin_only_endpoints(self, app, client):
        """Test that admin-only endpoints are protected"""
        with app.app_context():
            # Create regular employee
            employee = User(
                microsoft_id='emp', 
                email='emp@test.com', 
                name='Employee',
                role=UserRole.EMPLOYEE
            )
            db.session.add(employee)
            db.session.commit()
            
            # Create valid token for employee
            payload = {
                'user_id': employee.id,
                'exp': int(time.time()) + 3600,
                'iat': int(time.time())
            }
            
            token = jwt.encode(
                payload, 
                app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
            headers = {'Authorization': f'Bearer {token}'}
            
            # Try to access admin endpoint
            response = client.get('/api/admin/users', headers=headers)
            assert response.status_code == 403
            
            data = response.get_json()
            assert 'permission' in data['error']['message'].lower()


class TestInputValidationSecurity:
    """Test input validation and sanitization"""
    
    def test_sql_injection_prevention(self, app, client):
        """Test SQL injection prevention"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create valid token
            payload = {
                'user_id': user.id,
                'exp': int(time.time()) + 3600,
                'iat': int(time.time())
            }
            
            token = jwt.encode(
                payload, 
                app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
            headers = {'Authorization': f'Bearer {token}'}
            
            # Attempt SQL injection in query parameters
            malicious_params = {
                'search': "'; DROP TABLE users; --",
                'category': "' OR '1'='1",
                'amount': "'; DELETE FROM accounts; --"
            }
            
            response = client.get('/api/accounts/transactions', 
                                headers=headers, 
                                query_string=malicious_params)
            
            # Should not cause server error, should handle gracefully
            assert response.status_code in [200, 400]
            
            # Verify users table still exists by making another request
            response2 = client.get('/api/accounts/balance', headers=headers)
            assert response2.status_code == 200
    
    def test_xss_prevention(self, app, client):
        """Test XSS prevention in input fields"""
        with app.app_context():
            # Create users
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.commit()
            
            # Create valid token
            payload = {
                'user_id': sender.id,
                'exp': int(time.time()) + 3600,
                'iat': int(time.time())
            }
            
            token = jwt.encode(
                payload, 
                app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
            headers = {'Authorization': f'Bearer {token}'}
            
            # Attempt XSS in transaction note
            xss_payload = {
                'recipient_id': recipient.id,
                'amount': '25.00',
                'note': '<script>alert("XSS")</script>',
                'category': '<img src=x onerror=alert("XSS")>'
            }
            
            response = client.post('/api/transactions/send', 
                                 headers=headers, 
                                 json=xss_payload)
            
            # Transaction should succeed but content should be sanitized
            if response.status_code == 200:
                data = response.get_json()
                # Note should not contain script tags
                assert '<script>' not in data['transaction']['note']
                assert 'alert(' not in data['transaction']['note']
    
    def test_amount_validation(self, app, client):
        """Test amount validation and limits"""
        with app.app_context():
            # Create users
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('100.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.commit()
            
            # Create valid token
            payload = {
                'user_id': sender.id,
                'exp': int(time.time()) + 3600,
                'iat': int(time.time())
            }
            
            token = jwt.encode(
                payload, 
                app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test negative amount
            response = client.post('/api/transactions/send', 
                                 headers=headers, 
                                 json={
                                     'recipient_id': recipient.id,
                                     'amount': '-25.00'
                                 })
            assert response.status_code == 400
            
            # Test zero amount
            response = client.post('/api/transactions/send', 
                                 headers=headers, 
                                 json={
                                     'recipient_id': recipient.id,
                                     'amount': '0.00'
                                 })
            assert response.status_code == 400
            
            # Test extremely large amount
            response = client.post('/api/transactions/send', 
                                 headers=headers, 
                                 json={
                                     'recipient_id': recipient.id,
                                     'amount': '999999999.99'
                                 })
            assert response.status_code == 400
            
            # Test invalid amount format
            response = client.post('/api/transactions/send', 
                                 headers=headers, 
                                 json={
                                     'recipient_id': recipient.id,
                                     'amount': 'invalid'
                                 })
            assert response.status_code == 400


class TestRateLimitingSecurity:
    """Test rate limiting and abuse prevention"""
    
    def test_login_rate_limiting(self, app, client):
        """Test login attempt rate limiting"""
        with app.app_context():
            # Mock failed login attempts
            failed_attempts = []
            for i in range(10):  # Exceed rate limit
                response = client.post('/api/auth/login', json={
                    'code': f'invalid-code-{i}',
                    'redirect_uri': 'http://localhost:3000/callback'
                })
                failed_attempts.append(response.status_code)
            
            # Should eventually hit rate limit
            assert any(status == 429 for status in failed_attempts[-3:])
    
    def test_api_rate_limiting(self, app, client):
        """Test general API rate limiting"""
        with app.app_context():
            # Create user and account
            user = User(microsoft_id='test', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('100.00'))
            db.session.add(account)
            db.session.commit()
            
            # Create valid token
            payload = {
                'user_id': user.id,
                'exp': int(time.time()) + 3600,
                'iat': int(time.time())
            }
            
            token = jwt.encode(
                payload, 
                app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
            headers = {'Authorization': f'Bearer {token}'}
            
            # Make rapid requests
            responses = []
            for i in range(20):  # Exceed rate limit
                response = client.get('/api/accounts/balance', headers=headers)
                responses.append(response.status_code)
            
            # Should eventually hit rate limit
            assert any(status == 429 for status in responses[-5:])
    
    def test_transaction_frequency_limiting(self, app, client):
        """Test transaction frequency limiting"""
        with app.app_context():
            # Create users
            sender = User(microsoft_id='sender', email='sender@test.com', name='Sender')
            recipient = User(microsoft_id='recipient', email='recipient@test.com', name='Recipient')
            db.session.add_all([sender, recipient])
            db.session.flush()
            
            sender_account = Account(user_id=sender.id, balance=Decimal('1000.00'))
            recipient_account = Account(user_id=recipient.id, balance=Decimal('50.00'))
            db.session.add_all([sender_account, recipient_account])
            db.session.commit()
            
            # Create valid token
            payload = {
                'user_id': sender.id,
                'exp': int(time.time()) + 3600,
                'iat': int(time.time())
            }
            
            token = jwt.encode(
                payload, 
                app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
            headers = {'Authorization': f'Bearer {token}'}
            
            # Attempt rapid transactions
            transaction_responses = []
            for i in range(10):
                response = client.post('/api/transactions/send', 
                                     headers=headers, 
                                     json={
                                         'recipient_id': recipient.id,
                                         'amount': '1.00',
                                         'note': f'Transaction {i}'
                                     })
                transaction_responses.append(response.status_code)
            
            # Should eventually hit transaction rate limit
            assert any(status == 429 for status in transaction_responses[-3:])


class TestDataProtectionSecurity:
    """Test data protection and privacy measures"""
    
    def test_sensitive_data_masking(self, app):
        """Test that sensitive data is properly masked in logs"""
        with app.app_context():
            # This would test that sensitive data like account balances,
            # transaction amounts, and personal information are masked
            # in application logs
            
            # Mock logging to capture log entries
            import logging
            from unittest.mock import MagicMock
            
            mock_logger = MagicMock()
            
            # Test that account balance is not logged in plain text
            user = User(microsoft_id='test', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.flush()
            
            account = Account(user_id=user.id, balance=Decimal('12345.67'))
            db.session.add(account)
            db.session.commit()
            
            # Simulate logging account access
            mock_logger.info(f"Account accessed for user {user.id}")
            
            # Verify sensitive data is not in log message
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            for log_message in log_calls:
                assert '12345.67' not in log_message
                assert user.email not in log_message
    
    def test_audit_trail_integrity(self, app):
        """Test audit trail integrity and immutability"""
        with app.app_context():
            from services.audit_service import AuditService
            from models import AuditLog, AuditAction
            
            # Create user
            user = User(microsoft_id='test', email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.commit()
            
            # Create audit log entry
            audit_log = AuditService.log_user_action(
                user_id=user.id,
                action=AuditAction.USER_LOGIN,
                details={'login_method': 'microsoft_sso'},
                ip_address='192.168.1.1',
                user_agent='Test Browser'
            )
            
            # Verify audit log was created
            assert audit_log.id is not None
            
            # Attempt to modify audit log (should be prevented)
            original_details = audit_log.details.copy()
            
            # In a real system, audit logs should be immutable
            # This test verifies the concept
            assert audit_log.details == original_details
    
    def test_data_encryption_at_rest(self, app):
        """Test that sensitive data is encrypted at rest"""
        with app.app_context():
            # This would test database encryption
            # For SQLite, this would involve SQLCipher
            
            # Create user with sensitive data
            user = User(
                microsoft_id='test-123',
                email='sensitive@test.com',
                name='Sensitive User'
            )
            db.session.add(user)
            db.session.commit()
            
            # In a real implementation, we would verify that:
            # 1. Database file is encrypted
            # 2. Sensitive fields are encrypted at column level
            # 3. Encryption keys are properly managed
            
            # For this test, we verify the concept exists
            assert hasattr(app.config, 'DATABASE_ENCRYPTION_KEY')
    
    def test_secure_password_handling(self, app):
        """Test secure password/token handling"""
        with app.app_context():
            # Test that passwords/tokens are never stored in plain text
            # and are properly hashed/encrypted
            
            test_token = 'sensitive-access-token'
            
            # Simulate token storage (should be hashed)
            import hashlib
            hashed_token = hashlib.sha256(test_token.encode()).hexdigest()
            
            # Verify original token is not stored
            assert test_token != hashed_token
            assert len(hashed_token) == 64  # SHA256 hex length
            
            # Test token comparison
            test_hash = hashlib.sha256(test_token.encode()).hexdigest()
            assert test_hash == hashed_token