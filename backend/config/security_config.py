"""
Security configuration for SoftBankCashWire
Defines security policies, rate limits, and fraud detection parameters
"""
import os
from datetime import timedelta

class SecurityConfig:
    """Security configuration settings"""
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')  # Use Redis in production
    
    # Default rate limits (requests per window)
    DEFAULT_RATE_LIMITS = {
        'user': {
            'limit': 100,
            'window_minutes': 60
        },
        'ip': {
            'limit': 200,
            'window_minutes': 60
        },
        'endpoint': {
            'limit': 1000,
            'window_minutes': 60
        }
    }
    
    # Endpoint-specific rate limits
    ENDPOINT_RATE_LIMITS = {
        'auth.login': {
            'user': {'limit': 5, 'window_minutes': 15},
            'ip': {'limit': 20, 'window_minutes': 15}
        },
        'transactions.send': {
            'user': {'limit': 50, 'window_minutes': 60},
            'ip': {'limit': 100, 'window_minutes': 60}
        },
        'money_requests.create': {
            'user': {'limit': 20, 'window_minutes': 60},
            'ip': {'limit': 50, 'window_minutes': 60}
        },
        'reporting.generate': {
            'user': {'limit': 10, 'window_minutes': 60},
            'ip': {'limit': 20, 'window_minutes': 60}
        }
    }
    
    # CSRF Protection Configuration
    CSRF_ENABLED = True
    CSRF_TOKEN_TIMEOUT = timedelta(hours=1)
    CSRF_EXEMPT_ENDPOINTS = [
        'auth.login_url',
        'auth.callback',
        'system.health',
        'system.ping'
    ]
    
    # Request Integrity Configuration
    REQUEST_INTEGRITY_ENABLED = True
    REQUEST_SIGNATURE_KEY = os.environ.get('REQUEST_SIGNATURE_KEY', 'dev-signature-key')
    REQUEST_SIGNATURE_ALGORITHM = 'sha256'
    
    # Fraud Detection Configuration
    FRAUD_DETECTION_ENABLED = True
    
    # Transaction fraud thresholds
    FRAUD_TRANSACTION_THRESHOLDS = {
        'unusual_amount_multiplier': 5,  # 5x average amount
        'max_amount_multiplier': 2,      # 2x previous maximum
        'daily_transaction_limit': 20,   # Transactions per day
        'rapid_transaction_seconds': 60, # Seconds between transactions
        'same_recipient_limit': 5,       # Same recipient in 7 days
        'round_number_threshold': 1000   # Round numbers above this amount
    }
    
    # Risk score thresholds
    FRAUD_RISK_THRESHOLDS = {
        'review_required': 50,
        'block_transaction': 80,
        'minimal_risk': 20,
        'low_risk': 40,
        'medium_risk': 70
    }
    
    # Login fraud thresholds
    FRAUD_LOGIN_THRESHOLDS = {
        'max_ip_addresses': 5,           # Different IPs in 7 days
        'failed_attempts_1h': 5,         # Failed attempts in 1 hour
        'failed_attempts_24h': 15,       # Failed attempts in 24 hours
        'unusual_hours_percentage': 0.3, # Percentage of logins at unusual hours
        'mfa_required_score': 30,        # Score requiring MFA
        'block_login_score': 60          # Score blocking login
    }
    
    # Security Headers Configuration
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }
    
    # Encryption Configuration
    ENCRYPTION_ENABLED = True
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'dev-encryption-key-32-chars-long')
    ENCRYPTION_ALGORITHM = 'AES-256-GCM'
    
    # Sensitive data fields to encrypt/mask
    SENSITIVE_FIELDS = [
        'password', 'secret', 'private_key', 'token', 'api_key',
        'account_number', 'routing_number', 'ssn', 'tax_id',
        'credit_card', 'bank_account', 'social_security'
    ]
    
    # IP Whitelist/Blacklist Configuration
    IP_WHITELIST_ENABLED = False
    IP_WHITELIST = []  # Add trusted IP ranges
    
    IP_BLACKLIST_ENABLED = True
    IP_BLACKLIST = []  # Add blocked IP ranges
    
    # Suspicious Activity Configuration
    SUSPICIOUS_ACTIVITY_THRESHOLDS = {
        'failed_attempts_1h': 10,
        'failed_attempts_24h': 50,
        'block_duration_minutes': 60
    }
    
    # Audit and Monitoring Configuration
    SECURITY_AUDIT_ENABLED = True
    SECURITY_MONITORING_ENABLED = True
    
    # Events to audit
    SECURITY_AUDIT_EVENTS = [
        'RATE_LIMIT_EXCEEDED',
        'CSRF_TOKEN_INVALID',
        'REQUEST_INTEGRITY_FAILED',
        'SUSPICIOUS_ACTIVITY_DETECTED',
        'TRANSACTION_BLOCKED_FRAUD',
        'LOGIN_BLOCKED_FRAUD',
        'MULTIPLE_FAILED_ATTEMPTS',
        'UNUSUAL_LOGIN_PATTERN'
    ]
    
    # Session Security Configuration
    SESSION_SECURITY = {
        'timeout_minutes': 480,          # 8 hours
        'refresh_threshold_minutes': 60, # Refresh if less than 1 hour remaining
        'concurrent_sessions_limit': 3,  # Max concurrent sessions per user
        'ip_binding_enabled': True,      # Bind session to IP
        'user_agent_binding_enabled': True # Bind session to user agent
    }
    
    # Password Security Configuration (if applicable)
    PASSWORD_SECURITY = {
        'min_length': 12,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special_chars': True,
        'max_age_days': 90,
        'history_count': 12,  # Remember last 12 passwords
        'lockout_attempts': 5,
        'lockout_duration_minutes': 30
    }
    
    # API Security Configuration
    API_SECURITY = {
        'require_https': True,
        'api_key_required': False,  # Using JWT instead
        'cors_origins': ['http://localhost:3000', 'https://softbank-cashwire.com'],
        'cors_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'cors_headers': ['Content-Type', 'Authorization', 'X-CSRF-Token'],
        'max_request_size': 10 * 1024 * 1024,  # 10MB
        'request_timeout_seconds': 30
    }
    
    # File Upload Security (if applicable)
    FILE_UPLOAD_SECURITY = {
        'max_file_size': 5 * 1024 * 1024,  # 5MB
        'allowed_extensions': ['.pdf', '.jpg', '.jpeg', '.png', '.csv'],
        'scan_for_malware': True,
        'quarantine_suspicious': True
    }
    
    # Database Security Configuration
    DATABASE_SECURITY = {
        'connection_encryption': True,
        'query_logging': True,
        'slow_query_threshold_seconds': 5,
        'connection_pool_size': 20,
        'connection_timeout_seconds': 30
    }

class DevelopmentSecurityConfig(SecurityConfig):
    """Development environment security configuration"""
    
    # Relaxed settings for development
    RATE_LIMIT_ENABLED = True
    CSRF_ENABLED = False  # Disabled for easier testing
    REQUEST_INTEGRITY_ENABLED = False
    FRAUD_DETECTION_ENABLED = True
    
    # More lenient rate limits
    DEFAULT_RATE_LIMITS = {
        'user': {'limit': 1000, 'window_minutes': 60},
        'ip': {'limit': 2000, 'window_minutes': 60},
        'endpoint': {'limit': 10000, 'window_minutes': 60}
    }
    
    # Allow HTTP in development
    API_SECURITY = {
        **SecurityConfig.API_SECURITY,
        'require_https': False
    }

class ProductionSecurityConfig(SecurityConfig):
    """Production environment security configuration"""
    
    # Strict settings for production
    RATE_LIMIT_ENABLED = True
    CSRF_ENABLED = True
    REQUEST_INTEGRITY_ENABLED = True
    FRAUD_DETECTION_ENABLED = True
    
    # Stricter rate limits
    DEFAULT_RATE_LIMITS = {
        'user': {'limit': 50, 'window_minutes': 60},
        'ip': {'limit': 100, 'window_minutes': 60},
        'endpoint': {'limit': 500, 'window_minutes': 60}
    }
    
    # Require HTTPS
    API_SECURITY = {
        **SecurityConfig.API_SECURITY,
        'require_https': True,
        'cors_origins': ['https://softbank-cashwire.com']
    }
    
    # Stricter fraud detection
    FRAUD_TRANSACTION_THRESHOLDS = {
        **SecurityConfig.FRAUD_TRANSACTION_THRESHOLDS,
        'daily_transaction_limit': 10,
        'rapid_transaction_seconds': 120
    }

class TestingSecurityConfig(SecurityConfig):
    """Testing environment security configuration"""
    
    # Minimal security for testing
    RATE_LIMIT_ENABLED = False
    CSRF_ENABLED = False
    REQUEST_INTEGRITY_ENABLED = False
    FRAUD_DETECTION_ENABLED = False
    
    # No rate limits for testing
    DEFAULT_RATE_LIMITS = {
        'user': {'limit': 10000, 'window_minutes': 60},
        'ip': {'limit': 20000, 'window_minutes': 60},
        'endpoint': {'limit': 100000, 'window_minutes': 60}
    }

def get_security_config(environment='development'):
    """Get security configuration for environment"""
    configs = {
        'development': DevelopmentSecurityConfig,
        'production': ProductionSecurityConfig,
        'testing': TestingSecurityConfig
    }
    
    return configs.get(environment, DevelopmentSecurityConfig)