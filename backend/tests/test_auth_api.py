"""
Tests for Authentication API endpoints
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from flask_jwt_extended import create_access_token, create_refresh_token
from models import db, User, UserRole, AccountStatus

class TestAuthAPI:
    """Test cases for Authentication API"""
    
    def test_get_login_url(self, client, app):
        """Test getting Microsoft login URL"""
        with app.app_context():
            response = client.get('/api/auth/login-url')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'login_url' in data
            assert 'state' in data
            assert 'redirect_uri' in data
            assert 'login.microsoftonline.com' in data['login_url']
    
    def test_get_login_url_with_redirect(self, client, app):
        """Test getting login URL with custom redirect URI"""
        with app.app_context():
            custom_redirect = 'http://example.com/callback'
            response = client.get(f'/api/auth/login-url?redirect_uri={custom_redirect}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['redirect_uri'] == custom_redirect
    
    @patch('api.auth.AuthService.exchange_code_for_token')
    @patch('api.auth.AuthService.authenticate_microsoft_sso')
    def test_auth_callback_success(self, mock_auth, mock_exchange, client, app):
        """Test successful authentication callback"""
        with app.app_context():
            # Mock token exchange
            mock_exchange.return_value = 'microsoft-access-token'
            
            # Mock authentication
            mock_auth.return_value = {
                'user': {
                    'id': 'user-123',
                    'email': 'test@company.com',
                    'name': 'Test User'
                },
                'access_token': 'jwt-access-token',
                'refresh_token': 'jwt-refresh-token',
                'expires_in': 3600
            }
            
            # Test callback
            response = client.post('/api/auth/callback', json={
                'code': 'auth-code',
                'redirect_uri': 'http://localhost:3000/callback'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'user' in data
            assert 'access_token' in data
            assert 'refresh_token' in data
            assert data['user']['email'] == 'test@company.com'
    
    def test_auth_callback_missing_data(self, client, app):
        """Test callback with missing required data"""
        with app.app_context():
            response = client.post('/api/auth/callback', json={
                'code': 'auth-code'
                # Missing redirect_uri
            })
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['error']['code'] == 'MISSING_FIELDS'
    
    @patch('api.auth.AuthService.authenticate_microsoft_sso')
    def test_authenticate_with_token_success(self, mock_auth, client, app):
        """Test direct token authentication"""
        with app.app_context():
            # Mock authentication
            mock_auth.return_value = {
                'user': {
                    'id': 'user-123',
                    'email': 'test@company.com',
                    'name': 'Test User'
                },
                'access_token': 'jwt-access-token',
                'refresh_token': 'jwt-refresh-token',
                'expires_in': 3600
            }
            
            # Test token authentication
            response = client.post('/api/auth/token', json={
                'access_token': 'microsoft-access-token'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'user' in data
            assert 'access_token' in data
    
    def test_authenticate_with_token_missing_token(self, client, app):
        """Test token authentication with missing token"""
        with app.app_context():
            response = client.post('/api/auth/token', json={})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['error']['code'] == 'MISSING_FIELDS'
    
    def test_refresh_token_success(self, client, app):
        """Test successful token refresh"""
        with app.app_context():
            # Create test user
            user = User(
                microsoft_id='test-123',
                email='test@company.com',
                name='Test User'
            )
            db.session.add(user)
            db.session.commit()
            
            # Create refresh token
            refresh_token = create_refresh_token(identity=user.id)
            
            # Test token refresh
            response = client.post('/api/auth/refresh', 
                                 headers={'Authorization': f'Bearer {refresh_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'access_token' in data
            assert 'expires_in' in data
    
    def test_refresh_token_no_token(self, client, app):
        """Test token refresh without token"""
        with app.app_context():
            response = client.post('/api/auth/refresh')
            
            assert response.status_code == 401
            data = json.loads(response.data)
            
            assert data['error']['code'] == 'TOKEN_REQUIRED'
    
    def test_get_current_user_success(self, client, app):
        """Test getting current user info"""
        with app.app_context():
            # Create test user
            user = User(
                microsoft_id='test-123',
                email='test@company.com',
                name='Test User',
                role=UserRole.EMPLOYEE
            )
            db.session.add(user)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test getting user info
            response = client.get('/api/auth/me',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'user' in data
            assert 'permissions' in data
            assert data['user']['email'] == 'test@company.com'
    
    def test_get_current_user_no_token(self, client, app):
        """Test getting user info without token"""
        with app.app_context():
            response = client.get('/api/auth/me')
            
            assert response.status_code == 401
    
    def test_validate_token_success(self, client, app):
        """Test token validation"""
        with app.app_context():
            # Create test user
            user = User(
                microsoft_id='test-123',
                email='test@company.com',
                name='Test User'
            )
            db.session.add(user)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test token validation
            response = client.get('/api/auth/validate',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['valid'] is True
            assert data['user_id'] == user.id
            assert data['email'] == user.email
    
    def test_get_user_permissions(self, client, app):
        """Test getting user permissions"""
        with app.app_context():
            # Create test user
            user = User(
                microsoft_id='test-123',
                email='test@company.com',
                name='Test User',
                role=UserRole.ADMIN
            )
            db.session.add(user)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test getting permissions
            response = client.get('/api/auth/permissions',
                                headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'permissions' in data
            assert data['permissions']['can_access_admin_features'] is True
    
    def test_logout_success(self, client, app):
        """Test successful logout"""
        with app.app_context():
            # Create test user
            user = User(
                microsoft_id='test-123',
                email='test@company.com',
                name='Test User'
            )
            db.session.add(user)
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            # Test logout
            response = client.post('/api/auth/logout',
                                 headers={'Authorization': f'Bearer {access_token}'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert 'message' in data
    
    def test_health_check(self, client, app):
        """Test authentication service health check"""
        with app.app_context():
            response = client.get('/api/auth/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['status'] == 'healthy'
            assert data['service'] == 'authentication'
            assert 'oauth_configured' in data
            assert 'database_connected' in data