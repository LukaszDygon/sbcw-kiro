"""
Audit API endpoints for SoftBankCashWire
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from services.audit_service import AuditService
from middleware.auth_middleware import auth_required, finance_required, admin_required
from models import db

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/logs', methods=['GET'])
@finance_required
@auth_required
def get_audit_logs():
    """
    Get audit logs with filtering and pagination (Finance team only)
    
    Query Parameters:
        - user_id: Filter by user ID
        - action_type: Filter by action type
        - entity_type: Filter by entity type
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
        - ip_address: Filter by IP address
        - severity: Filter by severity (INFO, WARNING, ERROR, CRITICAL)
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50, max: 1000)
        - include_system_events: Include system events (default: true)
    
    Returns:
        JSON with audit logs and pagination info
    """
    try:
        # Parse query parameters
        filters = {}
        
        if request.args.get('user_id'):
            filters['user_id'] = request.args.get('user_id')
        
        if request.args.get('action_type'):
            filters['action_type'] = request.args.get('action_type')
        
        if request.args.get('entity_type'):
            filters['entity_type'] = request.args.get('entity_type')
        
        if request.args.get('ip_address'):
            filters['ip_address'] = request.args.get('ip_address')
        
        if request.args.get('severity'):
            filters['severity'] = request.args.get('severity')
        
        # Date filters
        if request.args.get('start_date'):
            try:
                filters['start_date'] = datetime.fromisoformat(
                    request.args.get('start_date').replace('Z', '+00:00')
                )
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'start_date must be in ISO format'
                    }
                }), 400
        
        if request.args.get('end_date'):
            try:
                filters['end_date'] = datetime.fromisoformat(
                    request.args.get('end_date').replace('Z', '+00:00')
                )
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'end_date must be in ISO format'
                    }
                }), 400
        
        # Pagination
        if request.args.get('page'):
            try:
                filters['page'] = int(request.args.get('page'))
                if filters['page'] < 1:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_PAGE',
                        'message': 'Page must be a positive integer'
                    }
                }), 400
        
        if request.args.get('per_page'):
            try:
                filters['per_page'] = int(request.args.get('per_page'))
                if filters['per_page'] < 1 or filters['per_page'] > 1000:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_PER_PAGE',
                        'message': 'per_page must be between 1 and 1000'
                    }
                }), 400
        
        # Include system events
        filters['include_system_events'] = request.args.get('include_system_events', 'true').lower() == 'true'
        
        # Get audit logs
        result = AuditService.get_audit_logs(filters)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'AUDIT_LOGS_ERROR',
                'message': f'Failed to get audit logs: {str(e)}'
            }
        }), 500

@audit_bp.route('/reports/generate', methods=['POST'])
@finance_required
@auth_required
def generate_audit_report():
    """
    Generate comprehensive audit report (Finance team only)
    
    Expected JSON:
        {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "report_type": "COMPREHENSIVE"  // COMPREHENSIVE, TRANSACTIONS, SECURITY, USER_ACTIVITY
        }
    
    Returns:
        JSON with audit report data
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except (KeyError, ValueError):
            return jsonify({
                'error': {
                    'code': 'INVALID_DATES',
                    'message': 'start_date and end_date are required in ISO format'
                }
            }), 400
        
        # Validate date range
        if start_date >= end_date:
            return jsonify({
                'error': {
                    'code': 'INVALID_DATE_RANGE',
                    'message': 'start_date must be before end_date'
                }
            }), 400
        
        # Check if date range is too large (max 1 year)
        if (end_date - start_date).days > 365:
            return jsonify({
                'error': {
                    'code': 'DATE_RANGE_TOO_LARGE',
                    'message': 'Date range cannot exceed 365 days'
                }
            }), 400
        
        # Parse report type
        report_type = data.get('report_type', 'COMPREHENSIVE')
        valid_types = ['COMPREHENSIVE', 'TRANSACTIONS', 'SECURITY', 'USER_ACTIVITY']
        
        if report_type not in valid_types:
            return jsonify({
                'error': {
                    'code': 'INVALID_REPORT_TYPE',
                    'message': f'report_type must be one of: {", ".join(valid_types)}'
                }
            }), 400
        
        # Generate report
        report = AuditService.generate_audit_report(start_date, end_date, report_type)
        
        # Log report generation
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='AUDIT_REPORT_GENERATED',
            entity_type='AuditReport',
            new_values={
                'report_type': report_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'generated_by': g.current_user.name if g.current_user else 'Unknown'
            }
        )
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'REPORT_GENERATION_ERROR',
                'message': f'Failed to generate audit report: {str(e)}'
            }
        }), 500

@audit_bp.route('/statistics', methods=['GET'])
@finance_required
@auth_required
def get_audit_statistics():
    """
    Get audit statistics (Finance team only)
    
    Query Parameters:
        - days: Number of days to analyze (default: 30, max: 365)
    
    Returns:
        JSON with audit statistics
    """
    try:
        # Parse days parameter
        days = 30
        if request.args.get('days'):
            try:
                days = int(request.args.get('days'))
                if days < 1 or days > 365:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DAYS',
                        'message': 'Days must be between 1 and 365'
                    }
                }), 400
        
        # Get statistics
        statistics = AuditService.get_audit_statistics(days)
        
        return jsonify(statistics), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'STATISTICS_ERROR',
                'message': f'Failed to get audit statistics: {str(e)}'
            }
        }), 500

@audit_bp.route('/integrity/verify', methods=['POST'])
@admin_required
@auth_required
def verify_audit_integrity():
    """
    Verify audit log integrity (Admin only)
    
    Returns:
        JSON with integrity check results
    """
    try:
        # Perform integrity check
        integrity_results = AuditService.verify_audit_integrity()
        
        # Log integrity check
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='AUDIT_INTEGRITY_CHECK',
            entity_type='AuditSystem',
            new_values={
                'total_logs_checked': integrity_results['total_logs_checked'],
                'issues_found': len(integrity_results['integrity_issues']),
                'overall_status': integrity_results['overall_status'],
                'checked_by': g.current_user.name if g.current_user else 'Unknown'
            }
        )
        
        return jsonify(integrity_results), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'INTEGRITY_CHECK_ERROR',
                'message': f'Failed to verify audit integrity: {str(e)}'
            }
        }), 500

@audit_bp.route('/cleanup', methods=['POST'])
@admin_required
@auth_required
def cleanup_old_logs():
    """
    Clean up old audit logs based on retention policy (Admin only)
    
    Expected JSON:
        {
            "retention_days": 2555  // Optional, default: 2555 (7 years)
        }
    
    Returns:
        JSON with cleanup results
    """
    try:
        data = request.get_json() or {}
        
        # Parse retention days
        retention_days = data.get('retention_days', 2555)  # Default: 7 years
        
        try:
            retention_days = int(retention_days)
            if retention_days < 1:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({
                'error': {
                    'code': 'INVALID_RETENTION_DAYS',
                    'message': 'retention_days must be a positive integer'
                }
            }), 400
        
        # Minimum retention period check (e.g., 90 days)
        if retention_days < 90:
            return jsonify({
                'error': {
                    'code': 'RETENTION_TOO_SHORT',
                    'message': 'Retention period cannot be less than 90 days for compliance'
                }
            }), 400
        
        # Perform cleanup
        cleanup_result = AuditService.cleanup_old_audit_logs(retention_days)
        
        # Log cleanup operation
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='AUDIT_CLEANUP_PERFORMED',
            entity_type='AuditSystem',
            new_values={
                'retention_days': retention_days,
                'deleted_count': cleanup_result['deleted_count'],
                'success': cleanup_result['success'],
                'performed_by': g.current_user.name if g.current_user else 'Unknown'
            }
        )
        
        return jsonify(cleanup_result), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CLEANUP_ERROR',
                'message': f'Failed to cleanup audit logs: {str(e)}'
            }
        }), 500

@audit_bp.route('/action-types', methods=['GET'])
@finance_required
@auth_required
def get_action_types():
    """
    Get available audit action types (Finance team only)
    
    Returns:
        JSON with categorized action types
    """
    try:
        action_types = AuditService.ACTION_TYPES
        
        return jsonify({
            'action_types': action_types,
            'total_categories': len(action_types),
            'total_action_types': sum(len(actions) for actions in action_types.values())
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'ACTION_TYPES_ERROR',
                'message': f'Failed to get action types: {str(e)}'
            }
        }), 500

@audit_bp.route('/export', methods=['POST'])
@finance_required
@auth_required
def export_audit_logs():
    """
    Export audit logs in various formats (Finance team only)
    
    Expected JSON:
        {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "format": "CSV",  // CSV, JSON
            "filters": {  // Optional additional filters
                "user_id": "user-123",
                "action_type": "TRANSACTION_CREATED"
            }
        }
    
    Returns:
        JSON with export data or download link
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': {
                    'code': 'MISSING_DATA',
                    'message': 'Request body is required'
                }
            }), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except (KeyError, ValueError):
            return jsonify({
                'error': {
                    'code': 'INVALID_DATES',
                    'message': 'start_date and end_date are required in ISO format'
                }
            }), 400
        
        # Parse format
        export_format = data.get('format', 'JSON').upper()
        if export_format not in ['CSV', 'JSON']:
            return jsonify({
                'error': {
                    'code': 'INVALID_FORMAT',
                    'message': 'Format must be CSV or JSON'
                }
            }), 400
        
        # Get filters
        filters = data.get('filters', {})
        filters.update({
            'start_date': start_date,
            'end_date': end_date,
            'per_page': 10000  # Large limit for export
        })
        
        # Get audit logs
        result = AuditService.get_audit_logs(filters)
        
        # Log export operation
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='AUDIT_LOGS_EXPORTED',
            entity_type='AuditSystem',
            new_values={
                'format': export_format,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'record_count': len(result['audit_logs']),
                'exported_by': g.current_user.name if g.current_user else 'Unknown'
            }
        )
        
        if export_format == 'JSON':
            return jsonify({
                'format': 'JSON',
                'data': result['audit_logs'],
                'metadata': {
                    'export_timestamp': datetime.utcnow().isoformat(),
                    'record_count': len(result['audit_logs']),
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
            }), 200
        
        elif export_format == 'CSV':
            # For CSV, return structured data that frontend can convert
            csv_data = []
            for log in result['audit_logs']:
                csv_row = {
                    'timestamp': log['created_at'],
                    'user_id': log.get('user_id', ''),
                    'user_name': log.get('user_name', ''),
                    'action_type': log['action_type'],
                    'entity_type': log['entity_type'],
                    'entity_id': log.get('entity_id', ''),
                    'ip_address': log.get('ip_address', ''),
                    'user_agent': log.get('user_agent', ''),
                    'severity': log.get('severity', 'INFO')
                }
                csv_data.append(csv_row)
            
            return jsonify({
                'format': 'CSV',
                'data': csv_data,
                'headers': list(csv_data[0].keys()) if csv_data else [],
                'metadata': {
                    'export_timestamp': datetime.utcnow().isoformat(),
                    'record_count': len(csv_data),
                    'date_range': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat()
                    }
                }
            }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'EXPORT_ERROR',
                'message': f'Failed to export audit logs: {str(e)}'
            }
        }), 500

# Error handlers for audit blueprint
@audit_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'error': {
            'code': 'BAD_REQUEST',
            'message': 'Invalid request format'
        }
    }), 400

@audit_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }
    }), 401

@audit_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    return jsonify({
        'error': {
            'code': 'FORBIDDEN',
            'message': 'Finance team access required'
        }
    }), 403

@audit_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    db.session.rollback()
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500