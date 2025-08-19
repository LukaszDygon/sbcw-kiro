"""
Security API endpoints for SoftBankCashWire
Provides security monitoring, threat detection, and compliance reporting
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from services.security_audit_service import SecurityAuditService
from middleware.auth_middleware import auth_required, admin_required, finance_required
from middleware.security_middleware import rate_limit, security_headers
from models import db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security_bp = Blueprint('security', __name__)

@security_bp.route('/threats/monitor', methods=['GET'])
@admin_required
@auth_required
@rate_limit(user_limit=10, window_minutes=60)
@security_headers
def monitor_threats():
    """
    Monitor real-time security threats (Admin only)
    
    Returns:
        JSON with current threat status
    """
    try:
        threat_status = SecurityAuditService.monitor_real_time_threats()
        
        return jsonify({
            'success': True,
            'data': threat_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error monitoring threats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to monitor security threats'
        }), 500

@security_bp.route('/analysis/events', methods=['POST'])
@finance_required
@auth_required
@rate_limit(user_limit=5, window_minutes=60)
@security_headers
def analyze_security_events():
    """
    Analyze security events for a time period (Finance team only)
    
    Expected JSON:
        {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z"
        }
    
    Returns:
        JSON with security event analysis
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except (KeyError, ValueError):
            return jsonify({
                'success': False,
                'error': 'start_date and end_date are required in ISO format'
            }), 400
        
        # Validate date range
        if start_date >= end_date:
            return jsonify({
                'success': False,
                'error': 'start_date must be before end_date'
            }), 400
        
        # Check if date range is reasonable (max 90 days)
        if (end_date - start_date).days > 90:
            return jsonify({
                'success': False,
                'error': 'Date range cannot exceed 90 days'
            }), 400
        
        # Perform security analysis
        analysis = SecurityAuditService.analyze_security_events(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing security events: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze security events'
        }), 500

@security_bp.route('/analysis/user/<user_id>', methods=['GET'])
@finance_required
@auth_required
@rate_limit(user_limit=20, window_minutes=60)
@security_headers
def analyze_user_behavior(user_id):
    """
    Analyze user behavior for anomalies (Finance team only)
    
    Query Parameters:
        - days: Number of days to analyze (default: 7, max: 30)
    
    Returns:
        JSON with user behavior analysis
    """
    try:
        # Parse days parameter
        days = 7
        if request.args.get('days'):
            try:
                days = int(request.args.get('days'))
                if days < 1 or days > 30:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Days must be between 1 and 30'
                }), 400
        
        # Perform user behavior analysis
        analysis = SecurityAuditService.detect_anomalous_behavior(user_id, days)
        
        return jsonify({
            'success': True,
            'data': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing user behavior: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze user behavior'
        }), 500

@security_bp.route('/compliance/report', methods=['POST'])
@admin_required
@auth_required
@rate_limit(user_limit=3, window_minutes=60)
@security_headers
def generate_compliance_report():
    """
    Generate security compliance report (Admin only)
    
    Expected JSON:
        {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z"
        }
    
    Returns:
        JSON with compliance report
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except (KeyError, ValueError):
            return jsonify({
                'success': False,
                'error': 'start_date and end_date are required in ISO format'
            }), 400
        
        # Validate date range
        if start_date >= end_date:
            return jsonify({
                'success': False,
                'error': 'start_date must be before end_date'
            }), 400
        
        # Generate compliance report
        report = SecurityAuditService.generate_security_compliance_report(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': report
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate compliance report'
        }), 500

@security_bp.route('/status', methods=['GET'])
@admin_required
@auth_required
@rate_limit(user_limit=30, window_minutes=60)
@security_headers
def get_security_status():
    """
    Get overall security status (Admin only)
    
    Returns:
        JSON with security status overview
    """
    try:
        # Get threat monitoring status
        threat_status = SecurityAuditService.monitor_real_time_threats()
        
        # Get recent security events (last 24 hours)
        end_date = datetime.now(datetime.UTC)
        start_date = end_date - timedelta(hours=24)
        
        recent_analysis = SecurityAuditService.analyze_security_events(start_date, end_date)
        
        status = {
            'timestamp': datetime.now(datetime.UTC).isoformat(),
            'overall_status': 'SECURE',
            'threat_level': threat_status['threat_level'],
            'active_threats': len(threat_status['active_threats']),
            'critical_alerts': len(threat_status['critical_alerts']),
            'recent_events': {
                'last_24h': recent_analysis['summary']['total_security_events'],
                'users_affected': recent_analysis['summary']['unique_users_affected'],
                'ips_involved': recent_analysis['summary']['unique_ips_involved']
            },
            'security_metrics': {
                'authentication_events': len([
                    event for event_type, events in recent_analysis['event_breakdown'].items()
                    if event_type == 'AUTHENTICATION'
                    for event in events
                ]),
                'transaction_security_events': len([
                    event for event_type, events in recent_analysis['event_breakdown'].items()
                    if event_type == 'TRANSACTION_SECURITY'
                    for event in events
                ]),
                'system_security_events': len([
                    event for event_type, events in recent_analysis['event_breakdown'].items()
                    if event_type == 'SYSTEM_SECURITY'
                    for event in events
                ])
            },
            'recommendations': recent_analysis['recommendations'][:5]  # Top 5 recommendations
        }
        
        # Determine overall status
        if threat_status['threat_level'] == 'CRITICAL' or len(threat_status['critical_alerts']) > 0:
            status['overall_status'] = 'CRITICAL'
        elif threat_status['threat_level'] == 'HIGH' or len(threat_status['active_threats']) > 3:
            status['overall_status'] = 'WARNING'
        elif threat_status['threat_level'] == 'MEDIUM':
            status['overall_status'] = 'CAUTION'
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting security status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get security status'
        }), 500

@security_bp.route('/alerts', methods=['GET'])
@admin_required
@auth_required
@rate_limit(user_limit=50, window_minutes=60)
@security_headers
def get_security_alerts():
    """
    Get current security alerts (Admin only)
    
    Query Parameters:
        - severity: Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
        - limit: Number of alerts to return (default: 50, max: 200)
    
    Returns:
        JSON with security alerts
    """
    try:
        # Parse query parameters
        severity_filter = request.args.get('severity')
        limit = 50
        
        if request.args.get('limit'):
            try:
                limit = int(request.args.get('limit'))
                if limit < 1 or limit > 200:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Limit must be between 1 and 200'
                }), 400
        
        # Get current threat status
        threat_status = SecurityAuditService.monitor_real_time_threats()
        
        alerts = []
        
        # Add critical alerts
        for alert in threat_status['critical_alerts']:
            if not severity_filter or alert['severity'] == severity_filter:
                alerts.append({
                    'id': f"alert_{len(alerts)}",
                    'type': alert['type'],
                    'severity': alert['severity'],
                    'description': alert['description'],
                    'count': alert.get('count', 1),
                    'timestamp': alert.get('timestamp', datetime.now(datetime.UTC).isoformat()),
                    'status': 'ACTIVE'
                })
        
        # Add active threat alerts
        for threat in threat_status['active_threats']:
            if not severity_filter or threat['severity'] == severity_filter:
                alerts.append({
                    'id': f"threat_{len(alerts)}",
                    'type': threat['type'],
                    'severity': threat['severity'],
                    'description': threat['description'],
                    'count': threat.get('count', 1),
                    'timestamp': datetime.now(datetime.UTC).isoformat(),
                    'status': 'ACTIVE'
                })
        
        # Sort by severity and timestamp
        severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        alerts.sort(key=lambda x: (severity_order.get(x['severity'], 0), x['timestamp']), reverse=True)
        
        # Limit results
        alerts = alerts[:limit]
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': alerts,
                'total_count': len(alerts),
                'active_count': len([a for a in alerts if a['status'] == 'ACTIVE']),
                'critical_count': len([a for a in alerts if a['severity'] == 'CRITICAL']),
                'timestamp': datetime.now(datetime.UTC).isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting security alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get security alerts'
        }), 500

@security_bp.route('/config', methods=['GET'])
@admin_required
@auth_required
@security_headers
def get_security_config():
    """
    Get current security configuration (Admin only)
    
    Returns:
        JSON with security configuration
    """
    try:
        from config.security_config import get_security_config
        import os
        
        environment = os.environ.get('FLASK_ENV', 'development')
        config = get_security_config(environment)
        
        # Return non-sensitive configuration information
        config_info = {
            'environment': environment,
            'rate_limiting': {
                'enabled': config.RATE_LIMIT_ENABLED,
                'default_limits': config.DEFAULT_RATE_LIMITS
            },
            'csrf_protection': {
                'enabled': config.CSRF_ENABLED
            },
            'fraud_detection': {
                'enabled': config.FRAUD_DETECTION_ENABLED,
                'transaction_thresholds': config.FRAUD_TRANSACTION_THRESHOLDS,
                'risk_thresholds': config.FRAUD_RISK_THRESHOLDS
            },
            'security_headers': config.SECURITY_HEADERS,
            'session_security': config.SESSION_SECURITY,
            'api_security': {
                'require_https': config.API_SECURITY['require_https'],
                'cors_origins': config.API_SECURITY['cors_origins'],
                'max_request_size': config.API_SECURITY['max_request_size']
            }
        }
        
        return jsonify({
            'success': True,
            'data': config_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting security config: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get security configuration'
        }), 500

@security_bp.route('/health', methods=['GET'])
def health_check():
    """Security service health check"""
    return jsonify({
        'success': True,
        'service': 'security',
        'status': 'healthy',
        'timestamp': datetime.now(datetime.UTC).isoformat(),
        'features': {
            'threat_monitoring': True,
            'fraud_detection': True,
            'compliance_reporting': True,
            'real_time_alerts': True
        }
    }), 200

# Error handlers for security blueprint
@security_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'success': False,
        'error': 'Invalid request format'
    }), 400

@security_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'success': False,
        'error': 'Authentication required'
    }), 401

@security_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    return jsonify({
        'success': False,
        'error': 'Admin access required'
    }), 403

@security_bp.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit errors"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded. Please try again later.'
    }), 429

@security_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500