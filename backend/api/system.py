"""
System API endpoints for SoftBankCashWire
Provides health checks, API documentation, and system information
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from models import db, User, Account, Transaction, EventAccount, MoneyRequest, AuditLog
from services.auth_service import AuthService
from middleware.auth_middleware import auth_required, admin_required
import os
import sys

system_bp = Blueprint('system', __name__)

@system_bp.route('/health', methods=['GET'])
def health_check():
    """
    Comprehensive system health check
    
    Returns:
        JSON with system health status
    """
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now(datetime.UTC).isoformat(),
            'version': '1.0.0',
            'environment': os.environ.get('FLASK_ENV', 'production'),
            'checks': {}
        }
        
        # Database connectivity check
        try:
            db.session.execute('SELECT 1')
            health_status['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            health_status['status'] = 'unhealthy'
        
        # Authentication service check
        try:
            # Check if Microsoft OAuth is configured
            client_id = os.environ.get('MICROSOFT_CLIENT_ID')
            client_secret = os.environ.get('MICROSOFT_CLIENT_SECRET')
            
            if client_id and client_secret:
                health_status['checks']['authentication'] = {
                    'status': 'healthy',
                    'message': 'Microsoft OAuth configured'
                }
            else:
                health_status['checks']['authentication'] = {
                    'status': 'warning',
                    'message': 'Microsoft OAuth not fully configured'
                }
        except Exception as e:
            health_status['checks']['authentication'] = {
                'status': 'unhealthy',
                'message': f'Authentication service error: {str(e)}'
            }
            health_status['status'] = 'unhealthy'
        
        # System resources check
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status['checks']['resources'] = {
                'status': 'healthy' if cpu_percent < 80 and memory.percent < 80 and disk.percent < 80 else 'warning',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent
            }
        except ImportError:
            health_status['checks']['resources'] = {
                'status': 'unknown',
                'message': 'psutil not available for resource monitoring'
            }
        except Exception as e:
            health_status['checks']['resources'] = {
                'status': 'error',
                'message': f'Resource check failed: {str(e)}'
            }
        
        return jsonify(health_status), 200 if health_status['status'] == 'healthy' else 503
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now(datetime.UTC).isoformat(),
            'error': f'Health check failed: {str(e)}'
        }), 503

@system_bp.route('/info', methods=['GET'])
@auth_required
def system_info():
    """
    Get system information (authenticated users only)
    
    Returns:
        JSON with system information
    """
    try:
        info = {
            'application': {
                'name': 'SoftBankCashWire',
                'version': '1.0.0',
                'description': 'Internal banking system for SoftBank employees',
                'environment': os.environ.get('FLASK_ENV', 'production')
            },
            'runtime': {
                'python_version': sys.version,
                'platform': sys.platform,
                'timestamp': datetime.now(datetime.UTC).isoformat()
            },
            'features': {
                'microsoft_sso': bool(os.environ.get('MICROSOFT_CLIENT_ID')),
                'audit_logging': True,
                'reporting': True,
                'event_accounts': True,
                'money_requests': True
            }
        }
        
        return jsonify(info), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'SYSTEM_INFO_ERROR',
                'message': f'Failed to get system info: {str(e)}'
            }
        }), 500

@system_bp.route('/statistics', methods=['GET'])
@admin_required
@auth_required
def system_statistics():
    """
    Get system usage statistics (Admin only)
    
    Returns:
        JSON with system statistics
    """
    try:
        stats = {
            'timestamp': datetime.now(datetime.UTC).isoformat(),
            'users': {
                'total': User.query.count(),
                'active': User.query.filter_by(account_status='ACTIVE').count(),
                'by_role': {}
            },
            'accounts': {
                'total': Account.query.count(),
                'total_balance': str(db.session.query(db.func.sum(Account.balance)).scalar() or 0)
            },
            'transactions': {
                'total': Transaction.query.count(),
                'completed': Transaction.query.filter_by(status='COMPLETED').count(),
                'total_volume': str(db.session.query(db.func.sum(Transaction.amount)).filter_by(status='COMPLETED').scalar() or 0)
            },
            'events': {
                'total': EventAccount.query.count(),
                'active': EventAccount.query.filter_by(status='ACTIVE').count(),
                'total_target': str(db.session.query(db.func.sum(EventAccount.target_amount)).scalar() or 0)
            },
            'money_requests': {
                'total': MoneyRequest.query.count(),
                'pending': MoneyRequest.query.filter_by(status='PENDING').count(),
                'approved': MoneyRequest.query.filter_by(status='APPROVED').count()
            },
            'audit_logs': {
                'total': AuditLog.query.count(),
                'last_24h': AuditLog.query.filter(
                    AuditLog.created_at >= datetime.now(datetime.UTC) - datetime.timedelta(days=1)
                ).count()
            }
        }
        
        # Get user counts by role
        from models import UserRole
        for role in UserRole:
            stats['users']['by_role'][role.value] = User.query.filter_by(role=role).count()
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'STATISTICS_ERROR',
                'message': f'Failed to get system statistics: {str(e)}'
            }
        }), 500

@system_bp.route('/api-docs', methods=['GET'])
def api_documentation():
    """
    Get API documentation
    
    Returns:
        JSON with API endpoint documentation
    """
    try:
        docs = {
            'title': 'SoftBankCashWire API Documentation',
            'version': '1.0.0',
            'description': 'REST API for SoftBank internal banking system',
            'base_url': request.host_url + 'api',
            'authentication': {
                'type': 'JWT Bearer Token',
                'description': 'Use Microsoft SSO to obtain JWT tokens',
                'endpoints': {
                    'login': 'POST /auth/login-url',
                    'callback': 'POST /auth/callback',
                    'refresh': 'POST /auth/refresh',
                    'logout': 'POST /auth/logout'
                }
            },
            'endpoints': {
                'authentication': {
                    'base_path': '/auth',
                    'endpoints': [
                        {
                            'path': '/login-url',
                            'method': 'GET',
                            'description': 'Get Microsoft OAuth login URL',
                            'auth_required': False
                        },
                        {
                            'path': '/callback',
                            'method': 'POST',
                            'description': 'Handle OAuth callback',
                            'auth_required': False
                        },
                        {
                            'path': '/token',
                            'method': 'POST',
                            'description': 'Authenticate with Microsoft token',
                            'auth_required': False
                        },
                        {
                            'path': '/refresh',
                            'method': 'POST',
                            'description': 'Refresh access token',
                            'auth_required': True
                        },
                        {
                            'path': '/logout',
                            'method': 'POST',
                            'description': 'Logout current user',
                            'auth_required': True
                        },
                        {
                            'path': '/me',
                            'method': 'GET',
                            'description': 'Get current user info',
                            'auth_required': True
                        }
                    ]
                },
                'accounts': {
                    'base_path': '/accounts',
                    'endpoints': [
                        {
                            'path': '/balance',
                            'method': 'GET',
                            'description': 'Get account balance',
                            'auth_required': True
                        },
                        {
                            'path': '/summary',
                            'method': 'GET',
                            'description': 'Get account summary',
                            'auth_required': True
                        },
                        {
                            'path': '/history',
                            'method': 'GET',
                            'description': 'Get transaction history with filtering',
                            'auth_required': True
                        },
                        {
                            'path': '/analytics',
                            'method': 'GET',
                            'description': 'Get spending analytics',
                            'auth_required': True
                        }
                    ]
                },
                'transactions': {
                    'base_path': '/transactions',
                    'endpoints': [
                        {
                            'path': '/send',
                            'method': 'POST',
                            'description': 'Send money to another user',
                            'auth_required': True
                        },
                        {
                            'path': '/send-bulk',
                            'method': 'POST',
                            'description': 'Send money to multiple recipients',
                            'auth_required': True
                        },
                        {
                            'path': '/validate',
                            'method': 'POST',
                            'description': 'Validate transaction before processing',
                            'auth_required': True
                        },
                        {
                            'path': '/{transaction_id}',
                            'method': 'GET',
                            'description': 'Get transaction details',
                            'auth_required': True
                        },
                        {
                            'path': '/recent',
                            'method': 'GET',
                            'description': 'Get recent transactions',
                            'auth_required': True
                        }
                    ]
                },
                'money_requests': {
                    'base_path': '/money-requests',
                    'endpoints': [
                        {
                            'path': '/create',
                            'method': 'POST',
                            'description': 'Create money request',
                            'auth_required': True
                        },
                        {
                            'path': '/{request_id}/respond',
                            'method': 'POST',
                            'description': 'Respond to money request',
                            'auth_required': True
                        },
                        {
                            'path': '/pending',
                            'method': 'GET',
                            'description': 'Get pending requests',
                            'auth_required': True
                        },
                        {
                            'path': '/sent',
                            'method': 'GET',
                            'description': 'Get sent requests',
                            'auth_required': True
                        },
                        {
                            'path': '/received',
                            'method': 'GET',
                            'description': 'Get received requests',
                            'auth_required': True
                        }
                    ]
                },
                'events': {
                    'base_path': '/events',
                    'endpoints': [
                        {
                            'path': '/create',
                            'method': 'POST',
                            'description': 'Create event account',
                            'auth_required': True
                        },
                        {
                            'path': '/{event_id}/contribute',
                            'method': 'POST',
                            'description': 'Contribute to event',
                            'auth_required': True
                        },
                        {
                            'path': '/active',
                            'method': 'GET',
                            'description': 'Get active events',
                            'auth_required': True
                        },
                        {
                            'path': '/my-events',
                            'method': 'GET',
                            'description': 'Get user\'s events',
                            'auth_required': True
                        },
                        {
                            'path': '/search',
                            'method': 'GET',
                            'description': 'Search events',
                            'auth_required': True
                        }
                    ]
                },
                'reporting': {
                    'base_path': '/reporting',
                    'endpoints': [
                        {
                            'path': '/available',
                            'method': 'GET',
                            'description': 'Get available reports',
                            'auth_required': True
                        },
                        {
                            'path': '/transaction-summary',
                            'method': 'POST',
                            'description': 'Generate transaction summary',
                            'auth_required': True
                        },
                        {
                            'path': '/user-activity',
                            'method': 'POST',
                            'description': 'Generate user activity report',
                            'auth_required': True,
                            'roles': ['ADMIN', 'FINANCE']
                        },
                        {
                            'path': '/personal-analytics',
                            'method': 'POST',
                            'description': 'Generate personal analytics',
                            'auth_required': True
                        }
                    ]
                },
                'audit': {
                    'base_path': '/audit',
                    'endpoints': [
                        {
                            'path': '/logs',
                            'method': 'GET',
                            'description': 'Get audit logs',
                            'auth_required': True,
                            'roles': ['FINANCE']
                        },
                        {
                            'path': '/reports/generate',
                            'method': 'POST',
                            'description': 'Generate audit report',
                            'auth_required': True,
                            'roles': ['FINANCE']
                        },
                        {
                            'path': '/integrity/verify',
                            'method': 'POST',
                            'description': 'Verify audit integrity',
                            'auth_required': True,
                            'roles': ['ADMIN']
                        }
                    ]
                }
            },
            'error_codes': {
                'AUTHENTICATION_FAILED': 'Authentication credentials are invalid',
                'INSUFFICIENT_PERMISSIONS': 'User lacks required permissions',
                'VALIDATION_ERROR': 'Input validation failed',
                'TRANSACTION_FAILED': 'Transaction processing failed',
                'ACCOUNT_NOT_FOUND': 'Account does not exist',
                'INSUFFICIENT_FUNDS': 'Account has insufficient balance',
                'RATE_LIMIT_EXCEEDED': 'Too many requests',
                'INTERNAL_ERROR': 'Internal server error'
            },
            'data_formats': {
                'datetime': 'ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)',
                'currency': 'Decimal string with 2 decimal places (e.g., "123.45")',
                'uuid': 'Standard UUID format (e.g., "123e4567-e89b-12d3-a456-426614174000")'
            }
        }
        
        return jsonify(docs), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'DOCS_ERROR',
                'message': f'Failed to get API documentation: {str(e)}'
            }
        }), 500

@system_bp.route('/version', methods=['GET'])
def version_info():
    """
    Get version information
    
    Returns:
        JSON with version details
    """
    return jsonify({
        'application': 'SoftBankCashWire',
        'version': '1.0.0',
        'build_date': '2024-01-01',
        'api_version': 'v1',
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'timestamp': datetime.now(datetime.UTC).isoformat()
    }), 200

@system_bp.route('/ping', methods=['GET'])
def ping():
    """
    Simple ping endpoint for basic connectivity testing
    
    Returns:
        JSON with pong response
    """
    return jsonify({
        'message': 'pong',
        'timestamp': datetime.now(datetime.UTC).isoformat(),
        'status': 'ok'
    }), 200

# Error handlers for system blueprint
@system_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Endpoint not found'
        }
    }), 404

@system_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500