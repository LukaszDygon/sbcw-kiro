"""
Security middleware for SoftBankCashWire
Provides comprehensive security features including rate limiting, CSRF protection,
fraud detection, and request/response encryption
"""
from functools import wraps
from flask import request, jsonify, g, current_app
from datetime import datetime, timedelta
from collections import defaultdict, deque
from decimal import Decimal
import hashlib
import hmac
import secrets
import json
import logging
from typing import Dict, List, Optional, Tuple
from models import User, Transaction, AuditLog, db
from services.audit_service import AuditService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Custom security error"""
    def __init__(self, message, code='SECURITY_ERROR', status_code=403):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class RateLimiter:
    """Advanced rate limiting with multiple strategies"""
    
    def __init__(self):
        # In-memory storage (use Redis in production)
        self.user_requests = defaultdict(deque)
        self.ip_requests = defaultdict(deque)
        self.endpoint_requests = defaultdict(deque)
        self.failed_attempts = defaultdict(list)
        
    def is_rate_limited(self, identifier: str, limit: int, window_minutes: int, 
                       request_store: Dict) -> Tuple[bool, int]:
        """
        Check if identifier is rate limited
        
        Args:
            identifier: Unique identifier (user_id, ip, etc.)
            limit: Maximum requests allowed
            window_minutes: Time window in minutes
            request_store: Storage for requests
            
        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        now = datetime.now(datetime.UTC)
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old requests
        while request_store[identifier] and request_store[identifier][0] <= window_start:
            request_store[identifier].popleft()
        
        current_count = len(request_store[identifier])
        
        if current_count >= limit:
            return True, 0
        
        # Add current request
        request_store[identifier].append(now)
        
        return False, limit - current_count - 1
    
    def check_user_rate_limit(self, user_id: str, limit: int = 100, 
                            window_minutes: int = 60) -> Tuple[bool, int]:
        """Check user-specific rate limit"""
        return self.is_rate_limited(user_id, limit, window_minutes, self.user_requests)
    
    def check_ip_rate_limit(self, ip_address: str, limit: int = 200, 
                          window_minutes: int = 60) -> Tuple[bool, int]:
        """Check IP-specific rate limit"""
        return self.is_rate_limited(ip_address, limit, window_minutes, self.ip_requests)
    
    def check_endpoint_rate_limit(self, endpoint: str, limit: int = 1000, 
                                window_minutes: int = 60) -> Tuple[bool, int]:
        """Check endpoint-specific rate limit"""
        return self.is_rate_limited(endpoint, limit, window_minutes, self.endpoint_requests)
    
    def record_failed_attempt(self, identifier: str, attempt_type: str = 'auth'):
        """Record failed authentication or transaction attempt"""
        now = datetime.now(datetime.UTC)
        self.failed_attempts[identifier].append({
            'timestamp': now,
            'type': attempt_type
        })
        
        # Clean old attempts (keep last 24 hours)
        cutoff = now - timedelta(hours=24)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt['timestamp'] > cutoff
        ]
    
    def get_failed_attempts(self, identifier: str, hours: int = 1) -> int:
        """Get number of failed attempts in specified time window"""
        cutoff = datetime.now(datetime.UTC) - timedelta(hours=hours)
        return len([
            attempt for attempt in self.failed_attempts[identifier]
            if attempt['timestamp'] > cutoff
        ])
    
    def is_suspicious_activity(self, identifier: str) -> bool:
        """Check for suspicious activity patterns"""
        # Check for too many failed attempts
        failed_1h = self.get_failed_attempts(identifier, 1)
        failed_24h = self.get_failed_attempts(identifier, 24)
        
        if failed_1h >= 10 or failed_24h >= 50:
            return True
        
        return False

class CSRFProtection:
    """CSRF protection for state-changing operations"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(token: str, expected_token: str) -> bool:
        """Validate CSRF token using constant-time comparison"""
        if not token or not expected_token:
            return False
        return hmac.compare_digest(token, expected_token)
    
    @staticmethod
    def get_csrf_token_from_request() -> Optional[str]:
        """Extract CSRF token from request headers or form data"""
        # Check header first
        token = request.headers.get('X-CSRF-Token')
        if token:
            return token
        
        # Check form data
        if request.is_json:
            data = request.get_json()
            if data and 'csrf_token' in data:
                return data['csrf_token']
        
        return None

class FraudDetection:
    """Fraud detection for financial transactions"""
    
    def __init__(self):
        self.suspicious_patterns = []
    
    def analyze_transaction(self, user_id: str, amount: Decimal, 
                          recipient_id: str = None) -> Dict:
        """
        Analyze transaction for fraud indicators
        
        Args:
            user_id: Sender user ID
            amount: Transaction amount
            recipient_id: Recipient user ID (optional)
            
        Returns:
            Dictionary with fraud analysis results
        """
        risk_score = 0
        risk_factors = []
        
        # Get user's recent transaction history
        recent_transactions = Transaction.query.filter(
            Transaction.sender_id == user_id,
            Transaction.created_at >= datetime.now(datetime.UTC) - timedelta(days=7),
            Transaction.status.in_(['COMPLETED', 'PENDING'])
        ).all()
        
        # Check for unusual amount patterns
        if recent_transactions:
            amounts = [t.amount for t in recent_transactions]
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            
            # Large deviation from normal spending
            if amount > avg_amount * 5:
                risk_score += 30
                risk_factors.append('UNUSUAL_AMOUNT_HIGH')
            
            # Significantly higher than previous maximum
            if amount > max_amount * 2:
                risk_score += 20
                risk_factors.append('AMOUNT_EXCEEDS_HISTORY')
        
        # Check transaction frequency
        today_transactions = [
            t for t in recent_transactions
            if t.created_at.date() == datetime.now(datetime.UTC).date()
        ]
        
        if len(today_transactions) > 20:
            risk_score += 40
            risk_factors.append('HIGH_FREQUENCY_TODAY')
        elif len(today_transactions) > 10:
            risk_score += 20
            risk_factors.append('MODERATE_FREQUENCY_TODAY')
        
        # Check for rapid successive transactions
        if len(recent_transactions) >= 2:
            last_transaction = max(recent_transactions, key=lambda t: t.created_at)
            time_since_last = datetime.now(datetime.UTC) - last_transaction.created_at
            
            if time_since_last.total_seconds() < 60:  # Less than 1 minute
                risk_score += 25
                risk_factors.append('RAPID_SUCCESSIVE_TRANSACTIONS')
        
        # Check for round number patterns (potential automation)
        if amount % 100 == 0 and amount >= 1000:
            risk_score += 10
            risk_factors.append('ROUND_NUMBER_PATTERN')
        
        # Check for same recipient frequency
        if recipient_id:
            same_recipient_count = len([
                t for t in recent_transactions
                if t.recipient_id == recipient_id
            ])
            
            if same_recipient_count > 5:
                risk_score += 15
                risk_factors.append('FREQUENT_SAME_RECIPIENT')
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'HIGH'
        elif risk_score >= 40:
            risk_level = 'MEDIUM'
        elif risk_score >= 20:
            risk_level = 'LOW'
        else:
            risk_level = 'MINIMAL'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'requires_review': risk_score >= 50,
            'block_transaction': risk_score >= 80
        }
    
    def analyze_login_pattern(self, user_id: str, ip_address: str, 
                            user_agent: str) -> Dict:
        """
        Analyze login pattern for suspicious activity
        
        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Dictionary with login analysis results
        """
        risk_score = 0
        risk_factors = []
        
        # Get recent login attempts from audit logs
        recent_logins = AuditLog.query.filter(
            AuditLog.user_id == user_id,
            AuditLog.action_type.in_(['USER_LOGIN', 'LOGIN_FAILED']),
            AuditLog.created_at >= datetime.now(datetime.UTC) - timedelta(days=7)
        ).order_by(AuditLog.created_at.desc()).limit(50).all()
        
        if recent_logins:
            # Check for IP address changes
            recent_ips = set()
            for log in recent_logins[:10]:  # Last 10 attempts
                if log.ip_address:
                    recent_ips.add(log.ip_address)
            
            if len(recent_ips) > 5:
                risk_score += 20
                risk_factors.append('MULTIPLE_IP_ADDRESSES')
            
            if ip_address not in recent_ips:
                risk_score += 15
                risk_factors.append('NEW_IP_ADDRESS')
            
            # Check for failed login attempts
            failed_logins = [
                log for log in recent_logins
                if log.action_type == 'LOGIN_FAILED'
            ]
            
            recent_failures = len([
                log for log in failed_logins
                if log.created_at >= datetime.now(datetime.UTC) - timedelta(hours=1)
            ])
            
            if recent_failures >= 5:
                risk_score += 30
                risk_factors.append('MULTIPLE_FAILED_ATTEMPTS')
            elif recent_failures >= 3:
                risk_score += 15
                risk_factors.append('SOME_FAILED_ATTEMPTS')
            
            # Check for unusual timing patterns
            login_hours = []
            for log in recent_logins:
                if log.action_type == 'USER_LOGIN':
                    login_hours.append(log.created_at.hour)
            
            if login_hours:
                # Check for logins at unusual hours (2 AM - 6 AM)
                unusual_hours = [h for h in login_hours if 2 <= h <= 6]
                if len(unusual_hours) > len(login_hours) * 0.3:
                    risk_score += 10
                    risk_factors.append('UNUSUAL_LOGIN_HOURS')
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = 'HIGH'
        elif risk_score >= 30:
            risk_level = 'MEDIUM'
        elif risk_score >= 15:
            risk_level = 'LOW'
        else:
            risk_level = 'MINIMAL'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'requires_mfa': risk_score >= 30,
            'block_login': risk_score >= 60
        }

class RequestEncryption:
    """Request/Response encryption for sensitive data"""
    
    @staticmethod
    def encrypt_sensitive_data(data: Dict) -> Dict:
        """Encrypt sensitive fields in response data"""
        sensitive_fields = [
            'account_number', 'routing_number', 'ssn', 'tax_id',
            'password', 'secret', 'private_key', 'token'
        ]
        
        if isinstance(data, dict):
            encrypted_data = {}
            for key, value in data.items():
                if key.lower() in sensitive_fields:
                    # In production, use proper encryption
                    encrypted_data[key] = '***ENCRYPTED***'
                elif isinstance(value, (dict, list)):
                    encrypted_data[key] = RequestEncryption.encrypt_sensitive_data(value)
                else:
                    encrypted_data[key] = value
            return encrypted_data
        elif isinstance(data, list):
            return [RequestEncryption.encrypt_sensitive_data(item) for item in data]
        else:
            return data
    
    @staticmethod
    def validate_request_integrity(request_data: str, signature: str, 
                                 secret_key: str) -> bool:
        """Validate request integrity using HMAC signature"""
        if not signature or not secret_key:
            return False
        
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            request_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

# Global instances
rate_limiter = RateLimiter()
fraud_detector = FraudDetection()

def rate_limit(user_limit: int = 100, ip_limit: int = 200, 
              endpoint_limit: int = 1000, window_minutes: int = 60):
    """
    Decorator for rate limiting with multiple strategies
    
    Args:
        user_limit: Requests per user per window
        ip_limit: Requests per IP per window
        endpoint_limit: Requests per endpoint per window
        window_minutes: Time window in minutes
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client info
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            
            endpoint = f"{request.method} {request.endpoint}"
            
            # Check IP rate limit
            ip_limited, ip_remaining = rate_limiter.check_ip_rate_limit(
                ip_address, ip_limit, window_minutes
            )
            
            if ip_limited:
                logger.warning(f"IP rate limit exceeded: {ip_address}")
                AuditService.log_security_event(
                    event_type='RATE_LIMIT_EXCEEDED',
                    ip_address=ip_address,
                    details={'limit_type': 'IP', 'limit': ip_limit}
                )
                return jsonify({
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': f'IP rate limit exceeded. Try again later.'
                    }
                }), 429
            
            # Check endpoint rate limit
            endpoint_limited, endpoint_remaining = rate_limiter.check_endpoint_rate_limit(
                endpoint, endpoint_limit, window_minutes
            )
            
            if endpoint_limited:
                logger.warning(f"Endpoint rate limit exceeded: {endpoint}")
                AuditService.log_security_event(
                    event_type='RATE_LIMIT_EXCEEDED',
                    ip_address=ip_address,
                    details={'limit_type': 'ENDPOINT', 'endpoint': endpoint}
                )
                return jsonify({
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': f'Endpoint rate limit exceeded. Try again later.'
                    }
                }), 429
            
            # Check user rate limit if authenticated
            if hasattr(g, 'current_user_id'):
                user_limited, user_remaining = rate_limiter.check_user_rate_limit(
                    g.current_user_id, user_limit, window_minutes
                )
                
                if user_limited:
                    logger.warning(f"User rate limit exceeded: {g.current_user_id}")
                    AuditService.log_user_action(
                        user_id=g.current_user_id,
                        action_type='RATE_LIMIT_EXCEEDED',
                        entity_type='SecurityEvent',
                        ip_address=ip_address,
                        new_values={'limit_type': 'USER', 'limit': user_limit}
                    )
                    return jsonify({
                        'error': {
                            'code': 'RATE_LIMIT_EXCEEDED',
                            'message': f'User rate limit exceeded. Try again later.'
                        }
                    }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def csrf_protect(f):
    """Decorator for CSRF protection on state-changing operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only protect state-changing methods
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            csrf_token = CSRFProtection.get_csrf_token_from_request()
            
            # Get expected token from session or user context
            expected_token = None
            if hasattr(g, 'current_user') and g.current_user:
                # In production, store CSRF token in secure session
                expected_token = getattr(g.current_user, 'csrf_token', None)
            
            if not CSRFProtection.validate_csrf_token(csrf_token, expected_token):
                logger.warning(f"CSRF token validation failed for {request.endpoint}")
                AuditService.log_security_event(
                    event_type='CSRF_TOKEN_INVALID',
                    user_id=getattr(g, 'current_user_id', None),
                    ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
                    details={'endpoint': request.endpoint}
                )
                return jsonify({
                    'error': {
                        'code': 'CSRF_TOKEN_INVALID',
                        'message': 'CSRF token validation failed'
                    }
                }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def fraud_detection(f):
    """Decorator for fraud detection on financial operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user_id'):
            return f(*args, **kwargs)
        
        # Analyze transaction if this is a financial endpoint
        if 'transaction' in request.endpoint or 'send' in request.endpoint:
            data = request.get_json() or {}
            amount = data.get('amount')
            recipient_id = data.get('recipient_id')
            
            if amount:
                try:
                    amount_decimal = Decimal(str(amount))
                    
                    # Perform fraud analysis
                    fraud_analysis = fraud_detector.analyze_transaction(
                        g.current_user_id, amount_decimal, recipient_id
                    )
                    
                    # Log fraud analysis
                    AuditService.log_user_action(
                        user_id=g.current_user_id,
                        action_type='FRAUD_ANALYSIS_PERFORMED',
                        entity_type='Transaction',
                        new_values={
                            'risk_score': fraud_analysis['risk_score'],
                            'risk_level': fraud_analysis['risk_level'],
                            'risk_factors': fraud_analysis['risk_factors']
                        }
                    )
                    
                    # Block high-risk transactions
                    if fraud_analysis['block_transaction']:
                        logger.warning(f"High-risk transaction blocked for user {g.current_user_id}")
                        AuditService.log_security_event(
                            event_type='TRANSACTION_BLOCKED_FRAUD',
                            user_id=g.current_user_id,
                            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
                            details=fraud_analysis
                        )
                        return jsonify({
                            'error': {
                                'code': 'TRANSACTION_BLOCKED',
                                'message': 'Transaction blocked due to security concerns'
                            }
                        }), 403
                    
                    # Add fraud analysis to request context
                    g.fraud_analysis = fraud_analysis
                    
                except (ValueError, TypeError):
                    pass  # Invalid amount format, let validation handle it
        
        return f(*args, **kwargs)
    
    return decorated_function

def security_headers(f):
    """Decorator to add security headers to responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add security headers
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    return decorated_function

def validate_request_integrity(f):
    """Decorator to validate request integrity using HMAC signatures"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only validate for sensitive operations
        if request.method in ['POST', 'PUT', 'DELETE'] and request.is_json:
            signature = request.headers.get('X-Request-Signature')
            secret_key = current_app.config.get('REQUEST_SIGNATURE_KEY')
            
            if signature and secret_key:
                request_data = request.get_data(as_text=True)
                
                if not RequestEncryption.validate_request_integrity(
                    request_data, signature, secret_key
                ):
                    logger.warning(f"Request integrity validation failed for {request.endpoint}")
                    AuditService.log_security_event(
                        event_type='REQUEST_INTEGRITY_FAILED',
                        user_id=getattr(g, 'current_user_id', None),
                        ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
                        details={'endpoint': request.endpoint}
                    )
                    return jsonify({
                        'error': {
                            'code': 'REQUEST_INTEGRITY_FAILED',
                            'message': 'Request integrity validation failed'
                        }
                    }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

class SecurityMiddleware:
    """Main security middleware class"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Process security checks before request"""
        # Skip security checks for certain paths
        skip_paths = ['/api/system/health', '/api/system/ping', '/api/system/version']
        
        if request.path in skip_paths:
            return
        
        # Check for suspicious activity
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        # Check if IP is in suspicious activity list
        if rate_limiter.is_suspicious_activity(ip_address):
            logger.warning(f"Suspicious activity detected from IP: {ip_address}")
            AuditService.log_security_event(
                event_type='SUSPICIOUS_ACTIVITY_DETECTED',
                ip_address=ip_address,
                details={'endpoint': request.endpoint, 'method': request.method}
            )
            return jsonify({
                'error': {
                    'code': 'SUSPICIOUS_ACTIVITY',
                    'message': 'Suspicious activity detected. Access temporarily restricted.'
                }
            }), 403
    
    def after_request(self, response):
        """Process security measures after request"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Encrypt sensitive data in responses
        if response.is_json and response.status_code == 200:
            try:
                data = response.get_json()
                if data:
                    encrypted_data = RequestEncryption.encrypt_sensitive_data(data)
                    response.data = json.dumps(encrypted_data)
            except Exception as e:
                logger.error(f"Error encrypting response data: {str(e)}")
        
        return response