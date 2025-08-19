"""
Tests for AuthService
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from services.auth_service import AuthService
from models import db, User, UserRole, AccountStatus, Account

class TestAuthService:
    """Test cases for AuthService"""
    
    @patch('services.auth_service.requests.get')
    def test_get_microsoft_user_info_success(self, mock_get, app):
        """Test successful Microsoft user info retrieval"""
        with app.app_context():
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'id': 'microsoft-123',
                'mail': 'test@company.com',
                'displayName': 'Test User'
            }
            mock_get.return_value = mock_response
            
            # Test the method
            user_info = AuthService._get_microsoft_user_info('fake-token')
            
            assert user_info['id'] == 'microsoft-123'
            assert user_info['mail'] == 'test@company.com'
            assert user_info['displayName'] == 'Test User'
            
            # Verify API call
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert 'https://graph.microsoft.com/v1.0/me' in args[0]
            assert kwargs['headers']['Authorization'] == 'Bearer fake-token'
    
    @patch('services.auth_service.requests.get')
    def test_get_microsoft_user_info_failure(self, mock_get, app):
        """Test Microsoft user info retrieval failure"""
        with app.app_context():
            # Mock failed API response
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response
            
            # Test the method
            with pytest.raises(ValueError, match="Microsoft Graph API error"):
                AuthService._get_microsoft_user_info('invalid-token')
    
    def test_find_or_create_user_existing(self, app):
        """Test finding existing user"""
        with app.app_context():
            # Create existing user
            existing_user = User(
                microsoft_id='existing-123',
                email='existing@company.com',
                name='Existing User'
            )
            db.session.add(existing_user)
            db.session.commit()
            
            # Test finding the user
            user_info = {
                'id': 'existing-123',
                'mail': 'existing@company.com',
                'displayName': 'Existing User'
            }
            
            found_user = AuthService._find_or_create_user(user_info)
            
            assert found_user.id == existing_user.id
            assert found_user.microsoft_id == 'existing-123'
            assert found_user.email == 'existing@company.com'
    
    def test_find_or_create_user_new(self, app):
        """Test creating new user"""
        with app.app_context():
            user_info = {
                'id': 'new-123',
                'mail': 'new@company.com',
                'displayName': 'New User'
            }
            
            # Test creating new user
            new_user = AuthService._find_or_create_user(user_info)
            
            assert new_user.microsoft_id == 'new-123'
            assert new_user.email == 'new@company.com'
            assert new_user.name == 'New User'
            assert new_user.role == UserRole.EMPLOYEE
            assert new_user.account_status == AccountStatus.ACTIVE
            
            # Verify account was created
            account = Account.query.filter_by(user_id=new_user.id).first()
            assert account is not None
            assert account.balance == Decimal('0.00')
    
    def test_validate_session_valid(self, app):
        """Test valid session validation"""
        with app.app_context():
            # Create user with recent login
            user = User(
                microsoft_id='test-123',
                email='test@company.com',
                name='Test User'
            )
            user.last_login = db.func.now()
            db.session.add(user)
            db.session.commit()
            
            # Test session validation
            is_valid = AuthService.validate_session(user.id)
            assert is_valid is True
    
    def test_validate_session_inactive_user(self, app):
        """Test session validation with inactive user"""
        with app.app_context():
            # Create inactive user
            user = User(
                microsoft_id='inactive-123',
                email='inactive@company.com',
                name='Inactive User',
                account_status=AccountStatus.SUSPENDED
            )
            db.session.add(user)
            db.session.commit()
            
            # Test session validation
            is_valid = AuthService.validate_session(user.id)
            assert is_valid is False
    
    def test_get_user_permissions_employee(self, app):
        """Test getting permissions for employee"""
        with app.app_context():
            # Create employee user
            user = User(
                microsoft_id='emp-123',
                email='employee@company.com',
                name='Employee User',
                role=UserRole.EMPLOYEE
            )
            db.session.add(user)
            db.session.commit()
            
            # Test permissions
            permissions = AuthService.get_user_permissions(user.id)
            
            assert permissions['can_view_account'] is True
            assert permissions['can_send_money'] is True
            assert permissions['can_access_admin_features'] is False
            assert permissions['can_access_finance_features'] is False
    
    def test_get_user_permissions_admin(self, app):
        """Test getting permissions for admin"""
        with app.app_context():
            # Create admin user
            user = User(
                microsoft_id='admin-123',
                email='admin@company.com',
                name='Admin User',
                role=UserRole.ADMIN
            )
            db.session.add(user)
            db.session.commit()
            
            # Test permissions
            permissions = AuthService.get_user_permissions(user.id)
            
            assert permissions['can_view_account'] is True
            assert permissions['can_access_admin_features'] is True
            assert permissions['can_manage_users'] is True
            assert permissions['can_access_finance_features'] is False
    
    def test_get_user_permissions_finance(self, app):
        """Test getting permissions for finance user"""
        with app.app_context():
            # Create finance user
            user = User(
                microsoft_id='finance-123',
                email='finance@company.com',
                name='Finance User',
                role=UserRole.FINANCE
            )
            db.session.add(user)
            db.session.commit()
            
            # Test permissions
            permissions = AuthService.get_user_permissions(user.id)
            
            assert permissions['can_view_account'] is True
            assert permissions['can_access_admin_features'] is True
            assert permissions['can_access_finance_features'] is True
            assert permissions['can_generate_reports'] is True
            assert permissions['can_view_all_transactions'] is True
    
    def test_require_role_employee(self, app):
        """Test role requirement for employee"""
        with app.app_context():
            # Create employee user
            user = User(
                microsoft_id='emp-123',
                email='employee@company.com',
                name='Employee User',
                role=UserRole.EMPLOYEE
            )
            db.session.add(user)
            db.session.commit()
            
            # Test role requirements
            assert AuthService.require_role(user.id, UserRole.EMPLOYEE) is True
            assert AuthService.require_role(user.id, UserRole.ADMIN) is False
            assert AuthService.require_role(user.id, UserRole.FINANCE) is False
    
    def test_require_role_admin(self, app):
        """Test role requirement for admin"""
        with app.app_context():
            # Create admin user
            user = User(
                microsoft_id='admin-123',
                email='admin@company.com',
                name='Admin User',
                role=UserRole.ADMIN
            )
            db.session.add(user)
            db.session.commit()
            
            # Test role requirements
            assert AuthService.require_role(user.id, UserRole.EMPLOYEE) is True
            assert AuthService.require_role(user.id, UserRole.ADMIN) is True
            assert AuthService.require_role(user.id, UserRole.FINANCE) is False
    
    def test_require_role_finance(self, app):
        """Test role requirement for finance"""
        with app.app_context():
            # Create finance user
            user = User(
                microsoft_id='finance-123',
                email='finance@company.com',
                name='Finance User',
                role=UserRole.FINANCE
            )
            db.session.add(user)
            db.session.commit()
            
            # Test role requirements
            assert AuthService.require_role(user.id, UserRole.EMPLOYEE) is True
            assert AuthService.require_role(user.id, UserRole.ADMIN) is True
            assert AuthService.require_role(user.id, UserRole.FINANCE) is True
    
    def test_logout_user(self, app):
        """Test user logout"""
        with app.app_context():
            # Create user
            user = User(
                microsoft_id='test-123',
                email='test@company.com',
                name='Test User'
            )
            db.session.add(user)
            db.session.commit()
            
            # Test logout
            success = AuthService.logout_user(
                user_id=user.id,
                ip_address='127.0.0.1',
                user_agent='Test Agent'
            )
            
            assert success is True
    
    @patch('services.auth_service.requests.post')
    def test_exchange_code_for_token_success(self, mock_post, app):
        """Test successful code to token exchange"""
        with app.app_context():
            # Mock successful token response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'access_token': 'new-access-token',
                'token_type': 'Bearer',
                'expires_in': 3600
            }
            mock_post.return_value = mock_response
            
            # Test token exchange
            token = AuthService.exchange_code_for_token(
                code='auth-code',
                redirect_uri='http://localhost:3000/callback'
            )
            
            assert token == 'new-access-token'
            mock_post.assert_called_once()
    
    @patch('services.auth_service.requests.post')
    def test_exchange_code_for_token_failure(self, mock_post, app):
        """Test failed code to token exchange"""
        with app.app_context():
            # Mock failed token response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_post.return_value = mock_response
            
            # Test token exchange failure
            with pytest.raises(ValueError, match="Token exchange failed"):
                AuthService.exchange_code_for_token(
                    code='invalid-code',
                    redirect_uri='http://localhost:3000/callback'
                )