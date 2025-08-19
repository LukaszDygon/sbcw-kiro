"""
Authentication middleware for SoftBankCashWire
Provides decorators and middleware for protecting routes
"""
from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import User, UserRole
from services.auth_service import AuthService

class DevelopmentUser:
    """Mock user for development mode"""
    def __init__(self, user_id='dev-admin-001', role='ADMIN'):
        self.id = user_id
        self.microsoft_id = 'dev-microsoft-id'
        self.email = 'admin@dev.local'
        self.name = 'Development Admin'
        self.role = UserRole.ADMIN if role == 'ADMIN' else UserRole(role)
        self.account_status = 'ACTIVE'
        self.created_at = '2024-01-01T00:00:00Z'
        self.last_login = '2024-01-01T00:00:00Z'
    
    def is_active(self):
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'microsoft_id': self.microsoft_id,
            'email': self.email,
            'name': self.name,
            'role': self.role.value if hasattr(self.role, 'value') else self.role,
            'account_status': self.account_status,
            'created_at': self.created_at,
            'last_login': self.last_login
        }

def auth_required(f):
    """
    Decorator to require authentication for a route
    Sets g.current_user for use in the route
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if development mode with auth disabled
        if current_app.config.get('DISABLE_AUTH', False):
            
            # Get the real admin user from database
            try:
                admin_user = User.query.filter(
                    (User.email == 'admin@softbank.com') | 
                    (User.role == UserRole.ADMIN)
                ).first()
                
                if admin_user:
                    # Set real admin user in Flask g object
                    g.current_user = admin_user
                    g.current_user_id = admin_user.id
                else:
                    # Fallback to development user if no admin found
                    dev_user = DevelopmentUser(
                        user_id=current_app.config.get('DEV_USER_ID', 'dev-admin-001'),
                        role=current_app.config.get('DEV_USER_ROLE', 'ADMIN')
                    )
                    g.current_user = dev_user
                    g.current_user_id = dev_user.id
                    
            except Exception as e:
                # Fallback to development user on database error
                dev_user = DevelopmentUser(
                    user_id=current_app.config.get('DEV_USER_ID', 'dev-admin-001'),
                    role=current_app.config.get('DEV_USER_ROLE', 'ADMIN')
                )
                g.current_user = dev_user
                g.current_user_id = dev_user.id
            
            return f(*args, **kwargs)
        
        # Production authentication flow - use JWT
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            
            user_id = get_jwt_identity()
            
            if not user_id:
                return jsonify({
                    'error': {
                        'code': 'INVALID_TOKEN',
                        'message': 'Invalid authentication token'
                    }
                }), 401
            
            # Validate session
            if not AuthService.validate_session(user_id):
                return jsonify({
                    'error': {
                        'code': 'SESSION_EXPIRED',
                        'message': 'Session has expired'
                    }
                }), 401
            
            # Get user
            user = User.query.get(user_id)
            if not user or not user.is_active():
                return jsonify({
                    'error': {
                        'code': 'USER_INACTIVE',
                        'message': 'User account is not active'
                    }
                }), 401
            
            # Set current user in Flask g object
            g.current_user = user
            g.current_user_id = user_id
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'error': {
                    'code': 'TOKEN_REQUIRED',
                    'message': 'Authentication token required'
                }
            }), 401
    
    return decorated_function

def role_required(required_role: UserRole):
    """
    Decorator to require specific role for a route
    Must be used after @auth_required
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'error': {
                        'code': 'AUTH_REQUIRED',
                        'message': 'Authentication required'
                    }
                }), 401
            
            # Check if development mode with auth disabled
            if current_app.config.get('DISABLE_AUTH', False):
                return f(*args, **kwargs)
            
            if not AuthService.require_role(g.current_user_id, required_role):
                return jsonify({
                    'error': {
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'message': f'Role {required_role.value} required'
                    }
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    return role_required(UserRole.ADMIN)(f)

def finance_required(f):
    """Decorator to require finance role"""
    return role_required(UserRole.FINANCE)(f)

def get_client_info():
    """
    Get client IP address and user agent from request
    
    Returns:
        Tuple of (ip_address, user_agent)
    """
    # Get IP address (handle proxy headers)
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_address and ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()
    
    user_agent = request.headers.get('User-Agent', '')
    
    return ip_address, user_agent

def validate_request_data(required_fields):
    """
    Decorator to validate required fields in request JSON
    
    Args:
        required_fields: List of required field names
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': {
                        'code': 'INVALID_CONTENT_TYPE',
                        'message': 'Content-Type must be application/json'
                    }
                }), 400
            
            data = request.get_json()
            if data is None:
                return jsonify({
                    'error': {
                        'code': 'MISSING_DATA',
                        'message': 'Request body is required'
                    }
                }), 400
            
            missing_fields = []
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    'error': {
                        'code': 'MISSING_FIELDS',
                        'message': f'Missing required fields: {", ".join(missing_fields)}'
                    }
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_by_user(max_requests=100, window_minutes=60):
    """
    Decorator to rate limit requests by user
    Simple in-memory rate limiting (for production, use Redis)
    
    Args:
        max_requests: Maximum requests allowed
        window_minutes: Time window in minutes
    """
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # In-memory storage (use Redis in production)
    user_requests = defaultdict(list)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user_id'):
                return f(*args, **kwargs)  # Skip rate limiting if not authenticated
            
            user_id = g.current_user_id
            now = datetime.now(datetime.UTC)
            window_start = now - timedelta(minutes=window_minutes)
            
            # Clean old requests
            user_requests[user_id] = [
                req_time for req_time in user_requests[user_id]
                if req_time > window_start
            ]
            
            # Check rate limit
            if len(user_requests[user_id]) >= max_requests:
                return jsonify({
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': f'Rate limit exceeded. Maximum {max_requests} requests per {window_minutes} minutes.'
                    }
                }), 429
            
            # Add current request
            user_requests[user_id].append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

class AuthMiddleware:
    """
    Authentication middleware class for Flask app
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Process request before route handler"""
        # Skip auth for certain paths
        skip_paths = ['/api/auth/login', '/api/auth/callback', '/api/health']
        
        if request.path in skip_paths:
            return
        
        # Add CORS headers for preflight requests
        if request.method == 'OPTIONS':
            return
    
    def after_request(self, response):
        """Process response after route handler"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response