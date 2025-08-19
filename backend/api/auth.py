"""
Authentication API endpoints for SoftBankCashWire
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.auth_service import AuthService
from middleware.auth_middleware import get_client_info, validate_request_data, auth_required
from models import db, AuditLog
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login-url', methods=['GET'])
def get_login_url():
    """
    Get Microsoft OAuth login URL
    
    Returns:
        JSON with login URL and state parameter
    """
    try:
        # Generate state parameter for CSRF protection
        state = str(uuid.uuid4())
        
        # Get redirect URI from query params or use default
        redirect_uri = request.args.get('redirect_uri', 'http://localhost:3000/auth/callback')
        
        # Generate Microsoft OAuth URL
        login_url = AuthService.get_microsoft_auth_url(redirect_uri, state)
        
        return jsonify({
            'login_url': login_url,
            'state': state,
            'redirect_uri': redirect_uri
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'LOGIN_URL_ERROR',
                'message': f'Failed to generate login URL: {str(e)}'
            }
        }), 500

@auth_bp.route('/callback', methods=['POST'])
@validate_request_data(['code', 'redirect_uri'])
def auth_callback():
    """
    Handle Microsoft OAuth callback
    
    Expected JSON:
        {
            "code": "authorization_code",
            "redirect_uri": "redirect_uri_used",
            "state": "optional_state_parameter"
        }
    
    Returns:
        JSON with user info and JWT tokens
    """
    try:
        data = request.get_json()
        code = data['code']
        redirect_uri = data['redirect_uri']
        state = data.get('state')
        
        ip_address, user_agent = get_client_info()
        
        # Exchange code for access token
        microsoft_token = AuthService.exchange_code_for_token(code, redirect_uri)
        
        # Authenticate user with Microsoft token
        auth_result = AuthService.authenticate_microsoft_sso(
            access_token=microsoft_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(auth_result), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'AUTHENTICATION_FAILED',
                'message': str(e)
            }
        }), 401
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'AUTH_CALLBACK_ERROR',
                'message': f'Authentication callback failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/token', methods=['POST'])
@validate_request_data(['access_token'])
def authenticate_with_token():
    """
    Authenticate directly with Microsoft access token
    
    Expected JSON:
        {
            "access_token": "microsoft_graph_access_token"
        }
    
    Returns:
        JSON with user info and JWT tokens
    """
    try:
        data = request.get_json()
        microsoft_token = data['access_token']
        
        ip_address, user_agent = get_client_info()
        
        # Authenticate user with Microsoft token
        auth_result = AuthService.authenticate_microsoft_sso(
            access_token=microsoft_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(auth_result), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'AUTHENTICATION_FAILED',
                'message': str(e)
            }
        }), 401
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'TOKEN_AUTH_ERROR',
                'message': f'Token authentication failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """
    Refresh access token using refresh token
    
    Returns:
        JSON with new access token
    """
    try:
        user_id = get_jwt_identity()
        
        if not user_id:
            return jsonify({
                'error': {
                    'code': 'INVALID_REFRESH_TOKEN',
                    'message': 'Invalid refresh token'
                }
            }), 401
        
        # Generate new access token
        token_result = AuthService.refresh_token(user_id)
        
        return jsonify(token_result), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'REFRESH_FAILED',
                'message': str(e)
            }
        }), 401
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'REFRESH_ERROR',
                'message': f'Token refresh failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@auth_required
def logout():
    """
    Log out current user
    
    Returns:
        JSON confirmation of logout
    """
    try:
        from flask import g
        
        user_id = g.current_user_id
        ip_address, user_agent = get_client_info()
        
        # Log out user
        success = AuthService.logout_user(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            return jsonify({
                'message': 'Logged out successfully'
            }), 200
        else:
            return jsonify({
                'error': {
                    'code': 'LOGOUT_FAILED',
                    'message': 'Failed to log out user'
                }
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'LOGOUT_ERROR',
                'message': f'Logout failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/me', methods=['GET'])
@auth_required
def get_current_user():
    """
    Get current user information
    
    Returns:
        JSON with current user info and permissions
    """
    try:
        from flask import g
        
        user = g.current_user
        user_id = g.current_user_id
        
        # Get user permissions
        permissions = AuthService.get_user_permissions(user_id)
        
        return jsonify({
            'user': user.to_dict(),
            'permissions': permissions
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'USER_INFO_ERROR',
                'message': f'Failed to get user info: {str(e)}'
            }
        }), 500

@auth_bp.route('/validate', methods=['GET'])
@auth_required
def validate_token():
    """
    Validate current JWT token
    
    Returns:
        JSON confirmation that token is valid
    """
    try:
        from flask import g
        
        user = g.current_user
        
        return jsonify({
            'valid': True,
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': f'Token validation failed: {str(e)}'
            }
        }), 500

@auth_bp.route('/permissions', methods=['GET'])
@auth_required
def get_user_permissions():
    """
    Get current user permissions
    
    Returns:
        JSON with user permissions
    """
    try:
        from flask import g
        
        user_id = g.current_user_id
        permissions = AuthService.get_user_permissions(user_id)
        
        return jsonify({
            'permissions': permissions
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'PERMISSIONS_ERROR',
                'message': f'Failed to get permissions: {str(e)}'
            }
        }), 500

@auth_bp.route('/users/search', methods=['GET'])
@auth_required
def search_users():
    """
    Search users by name or email (for transaction recipients)
    
    Query Parameters:
        - q: Search term (required, minimum 2 characters)
        - limit: Maximum number of results (default: 10, max: 50)
        - exclude_self: Exclude current user from results (default: true)
    
    Returns:
        JSON with matching users
    """
    try:
        from flask import g
        from models import User, AccountStatus
        
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return jsonify({
                'error': {
                    'code': 'MISSING_SEARCH_TERM',
                    'message': 'Search term is required'
                }
            }), 400
        
        if len(search_term) < 2:
            return jsonify({
                'error': {
                    'code': 'SEARCH_TERM_TOO_SHORT',
                    'message': 'Search term must be at least 2 characters'
                }
            }), 400
        
        # Parse limit parameter
        limit = 10
        if request.args.get('limit'):
            try:
                limit = int(request.args.get('limit'))
                if limit < 1 or limit > 50:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_LIMIT',
                        'message': 'Limit must be between 1 and 50'
                    }
                }), 400
        
        # Parse exclude_self parameter
        exclude_self = request.args.get('exclude_self', 'true').lower() == 'true'
        
        # Build query
        query = User.query.filter(
            User.account_status == AccountStatus.ACTIVE,
            db.or_(
                User.name.ilike(f'%{search_term}%'),
                User.email.ilike(f'%{search_term}%')
            )
        )
        
        # Exclude current user if requested
        if exclude_self:
            query = query.filter(User.id != g.current_user_id)
        
        # Order by name and limit results
        users = query.order_by(User.name).limit(limit).all()
        
        # Format results (only return safe information)
        results = [
            {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role.value if user.role else 'EMPLOYEE'
            }
            for user in users
        ]
        
        return jsonify({
            'users': results,
            'search_term': search_term,
            'count': len(results)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'USER_SEARCH_ERROR',
                'message': f'Failed to search users: {str(e)}'
            }
        }), 500

@auth_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for authentication service
    
    Returns:
        JSON with service status
    """
    try:
        # Check if Microsoft OAuth is configured
        client_id = current_app.config.get('MICROSOFT_CLIENT_ID')
        client_secret = current_app.config.get('MICROSOFT_CLIENT_SECRET')
        
        oauth_configured = bool(client_id and client_secret)
        
        return jsonify({
            'status': 'healthy',
            'service': 'authentication',
            'oauth_configured': oauth_configured,
            'database_connected': True  # If we reach here, DB is working
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'authentication',
            'error': str(e)
        }), 500

# Error handlers for auth blueprint
@auth_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'error': {
            'code': 'BAD_REQUEST',
            'message': 'Invalid request format'
        }
    }), 400

@auth_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }
    }), 401

@auth_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    return jsonify({
        'error': {
            'code': 'FORBIDDEN',
            'message': 'Access denied'
        }
    }), 403

@auth_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    db.session.rollback()
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500