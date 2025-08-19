"""
Authentication service for SoftBankCashWire
Handles Microsoft SSO integration and JWT token management
"""
import requests
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from models import db, User, UserRole, AccountStatus, Account, AuditLog
from decimal import Decimal

class AuthService:
    """Service for handling authentication and authorization"""
    
    MICROSOFT_GRAPH_URL = "https://graph.microsoft.com/v1.0"
    MICROSOFT_LOGIN_URL = "https://login.microsoftonline.com"
    
    @classmethod
    def authenticate_microsoft_sso(cls, access_token: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        Authenticate user using Microsoft SSO access token
        
        Args:
            access_token: Microsoft Graph access token
            ip_address: Client IP address for audit logging
            user_agent: Client user agent for audit logging
            
        Returns:
            Dict containing user info and JWT tokens
            
        Raises:
            ValueError: If authentication fails
        """
        try:
            # Get user info from Microsoft Graph
            user_info = cls._get_microsoft_user_info(access_token)
            
            # Find or create user
            user = cls._find_or_create_user(user_info)
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log successful login
            AuditLog.log_login(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            db.session.commit()
            
            # Generate JWT tokens
            access_token_jwt = create_access_token(
                identity=user.id,
                additional_claims={
                    'role': user.role.value,
                    'email': user.email,
                    'name': user.name
                }
            )
            
            refresh_token_jwt = create_refresh_token(identity=user.id)
            
            return {
                'user': user.to_dict(),
                'access_token': access_token_jwt,
                'refresh_token': refresh_token_jwt,
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
            }
            
        except Exception as e:
            # Log failed login attempt
            if 'user_info' in locals() and user_info:
                AuditLog.log_system_event(
                    action_type='LOGIN_FAILED',
                    entity_type='User',
                    details={
                        'email': user_info.get('mail', 'unknown'),
                        'error': str(e),
                        'ip_address': ip_address
                    }
                )
                db.session.commit()
            
            raise ValueError(f"Authentication failed: {str(e)}")
    
    @classmethod
    def _get_microsoft_user_info(cls, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Microsoft Graph API
        
        Args:
            access_token: Microsoft Graph access token
            
        Returns:
            User information from Microsoft Graph
            
        Raises:
            ValueError: If API call fails
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{cls.MICROSOFT_GRAPH_URL}/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                raise ValueError(f"Microsoft Graph API error: {response.status_code}")
            
            user_info = response.json()
            
            # Validate required fields
            required_fields = ['id', 'mail', 'displayName']
            for field in required_fields:
                if field not in user_info:
                    raise ValueError(f"Missing required field: {field}")
            
            return user_info
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to connect to Microsoft Graph: {str(e)}")
    
    @classmethod
    def _find_or_create_user(cls, user_info: Dict[str, Any]) -> User:
        """
        Find existing user or create new one based on Microsoft user info
        
        Args:
            user_info: User information from Microsoft Graph
            
        Returns:
            User object
        """
        microsoft_id = user_info['id']
        email = user_info['mail']
        name = user_info['displayName']
        
        # Try to find existing user by Microsoft ID
        user = User.query.filter_by(microsoft_id=microsoft_id).first()
        
        if user:
            # Update user info if changed
            if user.email != email or user.name != name:
                old_values = {'email': user.email, 'name': user.name}
                user.email = email
                user.name = name
                
                # Log user info update
                AuditLog.log_user_action(
                    user_id=user.id,
                    action_type='USER_INFO_UPDATED',
                    entity_type='User',
                    entity_id=user.id,
                    old_values=old_values,
                    new_values={'email': email, 'name': name}
                )
            
            return user
        
        # Create new user
        user = User(
            microsoft_id=microsoft_id,
            email=email,
            name=name,
            role=UserRole.EMPLOYEE,  # Default role
            account_status=AccountStatus.ACTIVE
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create account for new user
        account = Account(
            user_id=user.id,
            balance=Decimal('0.00')
        )
        
        db.session.add(account)
        
        # Log user creation
        AuditLog.log_user_action(
            user_id=user.id,
            action_type='USER_CREATED',
            entity_type='User',
            entity_id=user.id,
            new_values=user.to_dict()
        )
        
        return user
    
    @classmethod
    def refresh_token(cls, refresh_token_identity: str) -> Dict[str, Any]:
        """
        Generate new access token using refresh token
        
        Args:
            refresh_token_identity: User ID from refresh token
            
        Returns:
            New access token information
            
        Raises:
            ValueError: If user not found or inactive
        """
        user = User.query.get(refresh_token_identity)
        
        if not user:
            raise ValueError("User not found")
        
        if not user.is_active():
            raise ValueError("User account is not active")
        
        # Generate new access token
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'role': user.role.value,
                'email': user.email,
                'name': user.name
            }
        )
        
        return {
            'access_token': access_token,
            'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
        }
    
    @classmethod
    def validate_session(cls, user_id: str) -> bool:
        """
        Validate if user session is still valid
        
        Args:
            user_id: User ID to validate
            
        Returns:
            True if session is valid, False otherwise
        """
        user = User.query.get(user_id)
        
        if not user:
            return False
        
        if not user.is_active():
            return False
        
        # Check if last login is within session timeout (8 hours)
        if user.last_login:
            session_timeout = timedelta(hours=8)
            if datetime.utcnow() - user.last_login > session_timeout:
                return False
        
        return True
    
    @classmethod
    def get_user_permissions(cls, user_id: str) -> Dict[str, bool]:
        """
        Get user permissions based on role
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of permissions
        """
        user = User.query.get(user_id)
        
        if not user or not user.is_active():
            return {}
        
        permissions = {
            'can_view_account': True,
            'can_send_money': True,
            'can_request_money': True,
            'can_create_events': True,
            'can_contribute_to_events': True,
            'can_view_personal_analytics': True,
            'can_access_admin_features': user.can_access_admin_features(),
            'can_access_finance_features': user.can_access_finance_features(),
            'can_manage_users': user.role == UserRole.ADMIN,
            'can_view_all_transactions': user.can_access_finance_features(),
            'can_generate_reports': user.can_access_finance_features(),
            'can_access_audit_logs': user.can_access_finance_features(),
            'can_manage_system': user.role == UserRole.ADMIN
        }
        
        return permissions
    
    @classmethod
    def logout_user(cls, user_id: str, ip_address: str = None, user_agent: str = None) -> bool:
        """
        Log out user and invalidate session
        
        Args:
            user_id: User ID to log out
            ip_address: Client IP address for audit logging
            user_agent: Client user agent for audit logging
            
        Returns:
            True if logout successful
        """
        try:
            # Log logout event
            AuditLog.log_user_action(
                user_id=user_id,
                action_type='LOGOUT',
                entity_type='User',
                entity_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.commit()
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def get_microsoft_auth_url(cls, redirect_uri: str, state: str = None) -> str:
        """
        Generate Microsoft OAuth authorization URL
        
        Args:
            redirect_uri: Redirect URI after authentication
            state: Optional state parameter for CSRF protection
            
        Returns:
            Microsoft OAuth authorization URL
        """
        tenant_id = current_app.config.get('MICROSOFT_TENANT_ID', 'common')
        client_id = current_app.config.get('MICROSOFT_CLIENT_ID')
        
        if not client_id:
            raise ValueError("Microsoft Client ID not configured")
        
        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': 'openid profile email User.Read',
            'response_mode': 'query'
        }
        
        if state:
            params['state'] = state
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        return f"{cls.MICROSOFT_LOGIN_URL}/{tenant_id}/oauth2/v2.0/authorize?{query_string}"
    
    @classmethod
    def exchange_code_for_token(cls, code: str, redirect_uri: str) -> str:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from Microsoft
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            Microsoft Graph access token
            
        Raises:
            ValueError: If token exchange fails
        """
        tenant_id = current_app.config.get('MICROSOFT_TENANT_ID', 'common')
        client_id = current_app.config.get('MICROSOFT_CLIENT_ID')
        client_secret = current_app.config.get('MICROSOFT_CLIENT_SECRET')
        
        if not all([client_id, client_secret]):
            raise ValueError("Microsoft OAuth credentials not configured")
        
        token_url = f"{cls.MICROSOFT_LOGIN_URL}/{tenant_id}/oauth2/v2.0/token"
        
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
            'scope': 'User.Read'
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=10)
            
            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.status_code}")
            
            token_data = response.json()
            
            if 'access_token' not in token_data:
                raise ValueError("No access token in response")
            
            return token_data['access_token']
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to exchange code for token: {str(e)}")
    
    @classmethod
    def require_role(cls, user_id: str, required_role: UserRole) -> bool:
        """
        Check if user has required role
        
        Args:
            user_id: User ID to check
            required_role: Required role
            
        Returns:
            True if user has required role
        """
        user = User.query.get(user_id)
        
        if not user or not user.is_active():
            return False
        
        # Admin and Finance roles have elevated permissions
        if required_role == UserRole.EMPLOYEE:
            return True  # All active users can access employee features
        elif required_role == UserRole.ADMIN:
            return user.role in [UserRole.ADMIN, UserRole.FINANCE]
        elif required_role == UserRole.FINANCE:
            return user.role == UserRole.FINANCE
        
        return user.role == required_role
    
    @classmethod
    def cleanup_expired_sessions(cls) -> Dict[str, Any]:
        """
        Clean up expired user sessions and tokens
        
        Returns:
            Dict with cleanup results
        """
        try:
            # For JWT-based sessions, we don't store session data in the database
            # This method would typically clean up any stored refresh tokens or session data
            # Since we're using stateless JWT tokens, we'll simulate cleanup
            
            # In a real implementation, you might:
            # 1. Clean up stored refresh tokens that have expired
            # 2. Remove blacklisted tokens that are old
            # 3. Clean up any session-related data
            
            # For now, we'll return a simulated result
            cleaned_count = 0
            
            # Log the cleanup operation
            from services.audit_service import AuditService
            AuditService.log_system_event(
                'SESSION_CLEANUP_PERFORMED',
                {
                    'cleaned_sessions': cleaned_count,
                    'cleanup_time': datetime.utcnow().isoformat()
                }
            )
            
            return {
                'success': True,
                'cleaned_count': cleaned_count,
                'message': f'Cleaned up {cleaned_count} expired sessions',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'cleaned_count': 0,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }