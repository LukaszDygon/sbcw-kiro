"""
Account management API endpoints for SoftBankCashWire
"""
from flask import Blueprint, request, jsonify, g
from decimal import Decimal, InvalidOperation
from datetime import datetime
from services.account_service import AccountService
from middleware.auth_middleware import auth_required, get_client_info, validate_request_data
from models import db, TransactionType

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/balance', methods=['GET'])
@auth_required
def get_balance():
    """
    Get current account balance for authenticated user
    
    Returns:
        JSON with current balance information
    """
    try:
        user_id = g.current_user_id
        
        balance = AccountService.get_account_balance(user_id)
        available_balance = AccountService.get_available_balance(user_id)
        
        return jsonify({
            'balance': str(balance),
            'available_balance': str(available_balance),
            'currency': 'GBP',
            'limits': {
                'minimum_balance': str(AccountService.MIN_BALANCE),
                'maximum_balance': str(AccountService.MAX_BALANCE),
                'overdraft_limit': str(abs(AccountService.MIN_BALANCE))
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'ACCOUNT_NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BALANCE_ERROR',
                'message': f'Failed to get balance: {str(e)}'
            }
        }), 500

@accounts_bp.route('/summary', methods=['GET'])
@auth_required
def get_account_summary():
    """
    Get comprehensive account summary for authenticated user
    
    Returns:
        JSON with account summary including recent activity
    """
    try:
        user_id = g.current_user_id
        
        summary = AccountService.get_account_summary(user_id)
        
        return jsonify(summary), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'ACCOUNT_NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'SUMMARY_ERROR',
                'message': f'Failed to get account summary: {str(e)}'
            }
        }), 500

@accounts_bp.route('/history', methods=['GET'])
@auth_required
def get_transaction_history():
    """
    Get transaction history for authenticated user with filtering
    
    Query Parameters:
        - start_date: Start date (ISO format)
        - end_date: End date (ISO format)
        - transaction_type: Filter by transaction type
        - category: Filter by category
        - min_amount: Minimum amount filter
        - max_amount: Maximum amount filter
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - sort_by: Sort field (default: 'created_at')
        - sort_order: Sort order 'asc' or 'desc' (default: 'desc')
    
    Returns:
        JSON with transaction history and pagination info
    """
    try:
        user_id = g.current_user_id
        
        # Parse query parameters
        filters = {}
        
        # Date filters
        if request.args.get('start_date'):
            try:
                filters['start_date'] = datetime.fromisoformat(request.args.get('start_date').replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'start_date must be in ISO format'
                    }
                }), 400
        
        if request.args.get('end_date'):
            try:
                filters['end_date'] = datetime.fromisoformat(request.args.get('end_date').replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'end_date must be in ISO format'
                    }
                }), 400
        
        # Transaction type filter
        if request.args.get('transaction_type'):
            try:
                filters['transaction_type'] = TransactionType(request.args.get('transaction_type'))
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_TRANSACTION_TYPE',
                        'message': 'Invalid transaction type'
                    }
                }), 400
        
        # Category filter
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        
        # Amount filters
        if request.args.get('min_amount'):
            try:
                filters['min_amount'] = Decimal(request.args.get('min_amount'))
            except (InvalidOperation, ValueError):
                return jsonify({
                    'error': {
                        'code': 'INVALID_AMOUNT',
                        'message': 'min_amount must be a valid number'
                    }
                }), 400
        
        if request.args.get('max_amount'):
            try:
                filters['max_amount'] = Decimal(request.args.get('max_amount'))
            except (InvalidOperation, ValueError):
                return jsonify({
                    'error': {
                        'code': 'INVALID_AMOUNT',
                        'message': 'max_amount must be a valid number'
                    }
                }), 400
        
        # Search term filter
        if request.args.get('search_term'):
            filters['search_term'] = request.args.get('search_term').strip()
        
        # Status filter
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        # Pagination filters
        if request.args.get('page'):
            try:
                filters['page'] = int(request.args.get('page'))
                if filters['page'] < 1:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_PAGE',
                        'message': 'page must be a positive integer'
                    }
                }), 400
        
        if request.args.get('per_page'):
            try:
                filters['per_page'] = int(request.args.get('per_page'))
                if filters['per_page'] < 1 or filters['per_page'] > 100:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_PER_PAGE',
                        'message': 'per_page must be between 1 and 100'
                    }
                }), 400
        
        # Sorting filters
        if request.args.get('sort_by'):
            filters['sort_by'] = request.args.get('sort_by')
        
        if request.args.get('sort_order'):
            sort_order = request.args.get('sort_order').lower()
            if sort_order not in ['asc', 'desc']:
                return jsonify({
                    'error': {
                        'code': 'INVALID_SORT_ORDER',
                        'message': 'sort_order must be "asc" or "desc"'
                    }
                }), 400
            filters['sort_order'] = sort_order
        
        # Get transaction history
        history = AccountService.get_transaction_history(user_id, filters)
        
        return jsonify(history), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'HISTORY_ERROR',
                'message': f'Failed to get transaction history: {str(e)}'
            }
        }), 500

@accounts_bp.route('/analytics', methods=['GET'])
@auth_required
def get_spending_analytics():
    """
    Get spending analytics for authenticated user
    
    Query Parameters:
        - period_days: Analysis period in days (default: 30, max: 365)
    
    Returns:
        JSON with spending analytics by category
    """
    try:
        user_id = g.current_user_id
        
        # Parse period parameter
        period_days = 30
        if request.args.get('period_days'):
            try:
                period_days = int(request.args.get('period_days'))
                if period_days < 1 or period_days > 365:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_PERIOD',
                        'message': 'period_days must be between 1 and 365'
                    }
                }), 400
        
        # Get analytics
        analytics = AccountService.get_spending_analytics(user_id, period_days)
        
        return jsonify(analytics), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'ANALYTICS_ERROR',
                'message': f'Failed to get spending analytics: {str(e)}'
            }
        }), 500

@accounts_bp.route('/validate-amount', methods=['POST'])
@auth_required
@validate_request_data(['amount'])
def validate_transaction_amount():
    """
    Validate if transaction amount is within account limits
    
    Expected JSON:
        {
            "amount": "50.00"  // Amount to validate (negative for debit)
        }
    
    Returns:
        JSON with validation results
    """
    try:
        user_id = g.current_user_id
        data = request.get_json()
        
        # Parse amount
        try:
            amount = Decimal(str(data['amount']))
        except (InvalidOperation, ValueError):
            return jsonify({
                'error': {
                    'code': 'INVALID_AMOUNT',
                    'message': 'Amount must be a valid number'
                }
            }), 400
        
        # Validate amount
        validation = AccountService.validate_transaction_limits(user_id, amount)
        
        return jsonify(validation), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'ACCOUNT_NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': f'Failed to validate amount: {str(e)}'
            }
        }), 500

@accounts_bp.route('/status', methods=['GET'])
@auth_required
def get_account_status():
    """
    Get account status and health information
    
    Returns:
        JSON with account status and recommendations
    """
    try:
        user_id = g.current_user_id
        
        status = AccountService.check_account_status(user_id)
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'STATUS_ERROR',
                'message': f'Failed to get account status: {str(e)}'
            }
        }), 500

@accounts_bp.route('/limits', methods=['GET'])
@auth_required
def get_account_limits():
    """
    Get account limits and thresholds
    
    Returns:
        JSON with account limits information
    """
    try:
        return jsonify({
            'limits': {
                'minimum_balance': str(AccountService.MIN_BALANCE),
                'maximum_balance': str(AccountService.MAX_BALANCE),
                'overdraft_limit': str(abs(AccountService.MIN_BALANCE)),
                'overdraft_warning_threshold': str(AccountService.OVERDRAFT_WARNING_THRESHOLD)
            },
            'currency': 'GBP',
            'description': {
                'minimum_balance': 'Lowest allowed balance (overdraft limit)',
                'maximum_balance': 'Highest allowed balance',
                'overdraft_limit': 'Maximum amount you can go into overdraft',
                'overdraft_warning_threshold': 'Balance level that triggers low balance warnings'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'LIMITS_ERROR',
                'message': f'Failed to get account limits: {str(e)}'
            }
        }), 500

# Error handlers for accounts blueprint
@accounts_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'error': {
            'code': 'BAD_REQUEST',
            'message': 'Invalid request format'
        }
    }), 400

@accounts_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }
    }), 401

@accounts_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Resource not found'
        }
    }), 404

@accounts_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    db.session.rollback()
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500