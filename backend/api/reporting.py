"""
Reporting API endpoints for SoftBankCashWire
Handles report generation and export functionality
"""
from flask import Blueprint, request, jsonify, make_response
from datetime import datetime, timedelta
from functools import wraps
from services.reporting_service import ReportingService
from services.auth_service import AuthService
from models import UserRole
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

reporting_bp = Blueprint('reporting', __name__, url_prefix='/api/reporting')

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user = AuthService.get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            return f(user, *args, **kwargs)
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({'error': 'Authentication failed'}), 401
    return decorated_function

def parse_date_parameter(date_str: str, param_name: str) -> datetime:
    """Parse date parameter from request"""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid {param_name} format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

@reporting_bp.route('/available', methods=['GET'])
@require_auth
def get_available_reports(current_user):
    """
    Get available reports for current user
    
    Returns:
        JSON response with available report types
    """
    try:
        reports = ReportingService.get_available_reports(current_user.role)
        
        return jsonify({
            'success': True,
            'reports': reports
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get available reports'
        }), 500

@reporting_bp.route('/transaction-summary', methods=['POST'])
@require_auth
def generate_transaction_summary(current_user):
    """
    Generate transaction summary report
    
    Request body:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        user_id (str, optional): User ID for user-specific report
        export_format (str, optional): Export format ('json', 'csv')
    
    Returns:
        JSON response with report data or exported file
    """
    try:
        data = request.get_json()
        
        # Parse and validate parameters
        start_date = parse_date_parameter(data.get('start_date'), 'start_date')
        end_date = parse_date_parameter(data.get('end_date'), 'end_date')
        user_id = data.get('user_id')
        export_format = data.get('export_format', 'json')
        
        # Validate parameters
        validation = ReportingService.validate_report_parameters('TRANSACTION_SUMMARY', {
            'start_date': start_date,
            'end_date': end_date,
            'user_id': user_id
        })
        
        if not validation['valid']:
            return jsonify({
                'success': False,
                'errors': validation['errors']
            }), 400
        
        # Check access permissions
        if not ReportingService.check_report_access(
            current_user.role, 'TRANSACTION_SUMMARY', user_id, current_user.id
        ):
            return jsonify({
                'success': False,
                'error': 'Access denied for this report'
            }), 403
        
        # Generate report
        report_data = ReportingService.generate_transaction_summary_report(
            start_date, end_date, user_id
        )
        
        # Handle export formats
        if export_format == 'csv':
            csv_data = ReportingService.export_to_csv(report_data)
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=transaction_summary_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
            return response
        
        elif export_format == 'pdf':
            pdf_data = ReportingService.export_to_pdf(report_data)
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=transaction_summary_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf'
            return response
        
        elif export_format == 'json':
            json_data = ReportingService.export_to_json(report_data)
            response = make_response(json_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=transaction_summary_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.json'
            return response
        
        # Default: return JSON response
        return jsonify({
            'success': True,
            'data': report_data
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error generating transaction summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate transaction summary report'
        }), 500

@reporting_bp.route('/user-activity', methods=['POST'])
@require_auth
def generate_user_activity_report(current_user):
    """
    Generate user activity report
    
    Request body:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        export_format (str, optional): Export format ('json', 'csv')
    
    Returns:
        JSON response with report data or exported file
    """
    try:
        data = request.get_json()
        
        # Parse and validate parameters
        start_date = parse_date_parameter(data.get('start_date'), 'start_date')
        end_date = parse_date_parameter(data.get('end_date'), 'end_date')
        export_format = data.get('export_format', 'json')
        
        # Validate parameters
        validation = ReportingService.validate_report_parameters('USER_ACTIVITY', {
            'start_date': start_date,
            'end_date': end_date
        })
        
        if not validation['valid']:
            return jsonify({
                'success': False,
                'errors': validation['errors']
            }), 400
        
        # Check access permissions
        if not ReportingService.check_report_access(current_user.role, 'USER_ACTIVITY'):
            return jsonify({
                'success': False,
                'error': 'Access denied for this report'
            }), 403
        
        # Generate report
        report_data = ReportingService.generate_user_activity_report(start_date, end_date)
        
        # Handle export formats
        if export_format == 'csv':
            csv_data = ReportingService.export_to_csv(report_data)
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=user_activity_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
            return response
        
        elif export_format == 'pdf':
            pdf_data = ReportingService.export_to_pdf(report_data)
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=user_activity_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf'
            return response
        
        elif export_format == 'json':
            json_data = ReportingService.export_to_json(report_data)
            response = make_response(json_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=user_activity_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.json'
            return response
        
        # Default: return JSON response
        return jsonify({
            'success': True,
            'data': report_data
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error generating user activity report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate user activity report'
        }), 500

@reporting_bp.route('/event-accounts', methods=['POST'])
@require_auth
def generate_event_account_report(current_user):
    """
    Generate event account report
    
    Request body:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        export_format (str, optional): Export format ('json', 'csv')
    
    Returns:
        JSON response with report data or exported file
    """
    try:
        data = request.get_json()
        
        # Parse and validate parameters
        start_date = parse_date_parameter(data.get('start_date'), 'start_date')
        end_date = parse_date_parameter(data.get('end_date'), 'end_date')
        export_format = data.get('export_format', 'json')
        
        # Validate parameters
        validation = ReportingService.validate_report_parameters('EVENT_ACCOUNT', {
            'start_date': start_date,
            'end_date': end_date
        })
        
        if not validation['valid']:
            return jsonify({
                'success': False,
                'errors': validation['errors']
            }), 400
        
        # Check access permissions
        if not ReportingService.check_report_access(current_user.role, 'EVENT_ACCOUNT'):
            return jsonify({
                'success': False,
                'error': 'Access denied for this report'
            }), 403
        
        # Generate report
        report_data = ReportingService.generate_event_account_report(start_date, end_date)
        
        # Handle export formats
        if export_format == 'csv':
            csv_data = ReportingService.export_to_csv(report_data)
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=event_accounts_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
            return response
        
        elif export_format == 'pdf':
            pdf_data = ReportingService.export_to_pdf(report_data)
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=event_accounts_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf'
            return response
        
        elif export_format == 'json':
            json_data = ReportingService.export_to_json(report_data)
            response = make_response(json_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=event_accounts_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.json'
            return response
        
        # Default: return JSON response
        return jsonify({
            'success': True,
            'data': report_data
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error generating event account report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate event account report'
        }), 500

@reporting_bp.route('/personal-analytics', methods=['POST'])
@require_auth
def generate_personal_analytics(current_user):
    """
    Generate personal analytics report
    
    Request body:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        user_id (str, optional): User ID (defaults to current user)
        export_format (str, optional): Export format ('json', 'csv')
    
    Returns:
        JSON response with analytics data or exported file
    """
    try:
        data = request.get_json()
        
        # Parse and validate parameters
        start_date = parse_date_parameter(data.get('start_date'), 'start_date')
        end_date = parse_date_parameter(data.get('end_date'), 'end_date')
        user_id = data.get('user_id', current_user.id)
        export_format = data.get('export_format', 'json')
        
        # Validate parameters
        validation = ReportingService.validate_report_parameters('PERSONAL_ANALYTICS', {
            'start_date': start_date,
            'end_date': end_date,
            'user_id': user_id
        })
        
        if not validation['valid']:
            return jsonify({
                'success': False,
                'errors': validation['errors']
            }), 400
        
        # Check access permissions
        if not ReportingService.check_report_access(
            current_user.role, 'PERSONAL_ANALYTICS', user_id, current_user.id
        ):
            return jsonify({
                'success': False,
                'error': 'Access denied for this report'
            }), 403
        
        # Generate analytics
        analytics_data = ReportingService.generate_personal_analytics(
            user_id, start_date, end_date
        )
        
        # Handle export formats
        if export_format == 'csv':
            csv_data = ReportingService.export_to_csv(analytics_data)
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=personal_analytics_{user_id}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'
            return response
        
        elif export_format == 'pdf':
            pdf_data = ReportingService.export_to_pdf(analytics_data)
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=personal_analytics_{user_id}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf'
            return response
        
        elif export_format == 'json':
            json_data = ReportingService.export_to_json(analytics_data)
            response = make_response(json_data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=personal_analytics_{user_id}_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.json'
            return response
        
        # Default: return JSON response
        return jsonify({
            'success': True,
            'data': analytics_data
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error generating personal analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate personal analytics'
        }), 500

@reporting_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for reporting service"""
    return jsonify({
        'success': True,
        'service': 'reporting',
        'status': 'healthy',
        'timestamp': datetime.now(datetime.UTC).isoformat()
    }), 200