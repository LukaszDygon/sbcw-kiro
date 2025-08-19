"""
Money Request API endpoints for SoftBankCashWire
"""
from flask import Blueprint, request, jsonify, g
from decimal import Decimal, InvalidOperation
from services.money_request_service import MoneyRequestService
from middleware.auth_middleware import auth_required, get_client_info, validate_request_data
from models import db, RequestStatus

money_requests_bp = Blueprint('money_requests', __name__)

@money_requests_bp.route('/create', methods=['POST'])
@auth_required
@validate_request_data(['recipient_id', 'amount'])
def create_money_request():
    """
    Create a new money request
    
    Expected JSON:
        {
            "recipient_id": "user-id",
            "amount": "50.00",
            "note": "Lunch payment",  // Optional
            "expires_in_days": 7  // Optional, default 7, max 30
        }
    
    Returns:
        JSON with request creation result
    """
    try:
        requester_id = g.current_user_id
        data = request.get_json()
        
        recipient_id = data['recipient_id']
        
        # Parse and validate amount
        try:
            amount = Decimal(str(data['amount']))
        except (InvalidOperation, ValueError):
            return jsonify({
                'error': {
                    'code': 'INVALID_AMOUNT',
                    'message': 'Amount must be a valid number'
                }
            }), 400
        
        note = data.get('note')
        expires_in_days = data.get('expires_in_days')
        
        # Validate note length
        if note and len(note) > 500:
            return jsonify({
                'error': {
                    'code': 'NOTE_TOO_LONG',
                    'message': 'Note cannot exceed 500 characters'
                }
            }), 400
        
        # Validate expires_in_days
        if expires_in_days is not None:
            try:
                expires_in_days = int(expires_in_days)
            except (ValueError, TypeError):
                return jsonify({
                    'error': {
                        'code': 'INVALID_EXPIRY',
                        'message': 'Expiry days must be a valid number'
                    }
                }), 400
        
        ip_address, user_agent = get_client_info()
        
        # Create money request
        result = MoneyRequestService.create_money_request(
            requester_id=requester_id,
            recipient_id=recipient_id,
            amount=amount,
            note=note,
            expires_in_days=expires_in_days,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(result), 201
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'REQUEST_CREATION_FAILED',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CREATE_REQUEST_ERROR',
                'message': f'Failed to create money request: {str(e)}'
            }
        }), 500

@money_requests_bp.route('/<request_id>/respond', methods=['POST'])
@auth_required
@validate_request_data(['approved'])
def respond_to_request(request_id):
    """
    Respond to a money request (approve or decline)
    
    Expected JSON:
        {
            "approved": true  // true to approve, false to decline
        }
    
    Returns:
        JSON with response result
    """
    try:
        user_id = g.current_user_id
        data = request.get_json()
        
        approved = data['approved']
        
        if not isinstance(approved, bool):
            return jsonify({
                'error': {
                    'code': 'INVALID_RESPONSE',
                    'message': 'Approved must be true or false'
                }
            }), 400
        
        ip_address, user_agent = get_client_info()
        
        # Respond to request
        result = MoneyRequestService.respond_to_request(
            request_id=request_id,
            user_id=user_id,
            approved=approved,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'RESPONSE_FAILED',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'RESPOND_ERROR',
                'message': f'Failed to respond to request: {str(e)}'
            }
        }), 500

@money_requests_bp.route('/<request_id>/cancel', methods=['POST'])
@auth_required
def cancel_request(request_id):
    """
    Cancel a money request (only by requester)
    
    Returns:
        JSON with cancellation result
    """
    try:
        user_id = g.current_user_id
        ip_address, user_agent = get_client_info()
        
        result = MoneyRequestService.cancel_request(
            request_id=request_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'CANCEL_FAILED',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CANCEL_ERROR',
                'message': f'Failed to cancel request: {str(e)}'
            }
        }), 500

@money_requests_bp.route('/<request_id>', methods=['GET'])
@auth_required
def get_request(request_id):
    """
    Get money request details by ID
    
    Returns:
        JSON with request details
    """
    try:
        user_id = g.current_user_id
        
        money_request = MoneyRequestService.get_request_by_id(request_id, user_id)
        
        if not money_request:
            return jsonify({
                'error': {
                    'code': 'REQUEST_NOT_FOUND',
                    'message': 'Money request not found or access denied'
                }
            }), 404
        
        return jsonify({
            'request': money_request.to_dict(include_names=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'GET_REQUEST_ERROR',
                'message': f'Failed to get request: {str(e)}'
            }
        }), 500

@money_requests_bp.route('/pending', methods=['GET'])
@auth_required
def get_pending_requests():
    """
    Get pending money requests for authenticated user (as recipient)
    
    Returns:
        JSON with pending requests
    """
    try:
        user_id = g.current_user_id
        
        pending_requests = MoneyRequestService.get_pending_requests_for_user(user_id)
        
        return jsonify({
            'requests': [req.to_dict(include_names=True) for req in pending_requests],
            'count': len(pending_requests)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'PENDING_REQUESTS_ERROR',
                'message': f'Failed to get pending requests: {str(e)}'
            }
        }), 500

@money_requests_bp.route('/sent', methods=['GET'])
@auth_required
def get_sent_requests():
    """
    Get money requests sent by authenticated user
    
    Query Parameters:
        - status: Filter by status (PENDING, APPROVED, DECLINED, EXPIRED)
        - limit: Number of requests to return (default: 50, max: 100)
        - offset: Number of requests to skip (default: 0)
    
    Returns:
        JSON with sent requests and pagination
    """
    try:
        user_id = g.current_user_id
        
        # Parse query parameters
        status = None
        if request.args.get('status'):
            try:
                status = RequestStatus(request.args.get('status'))
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Invalid status value'
                    }
                }), 400
        
        limit = 50
        if request.args.get('limit'):
            try:
                limit = int(request.args.get('limit'))
                if limit < 1 or limit > 100:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_LIMIT',
                        'message': 'Limit must be between 1 and 100'
                    }
                }), 400
        
        offset = 0
        if request.args.get('offset'):
            try:
                offset = int(request.args.get('offset'))
                if offset < 0:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_OFFSET',
                        'message': 'Offset must be non-negative'
                    }
                }), 400
        
        # Get sent requests
        result = MoneyRequestService.get_sent_requests(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'SENT_REQUESTS_ERROR',
                'message': f'Failed to get sent requests: {str(e)}'
            }
        }), 500

@money_requests_bp.route('/received', methods=['GET'])
@auth_required
def get_received_requests():
    """
    Get money requests received by authenticated user
    
    Query Parameters:
        - status: Filter by status (PENDING, APPROVED, DECLINED, EXPIRED)
        - limit: Number of requests to return (default: 50, max: 100)
        - offset: Number of requests to skip (default: 0)
    
    Returns:
        JSON with received requests and pagination
    """
    try:
        user_id = g.current_user_id
        
        # Parse query parameters (same as sent requests)
        status = None
        if request.args.get('status'):
            try:
                status = RequestStatus(request.args.get('status'))
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Invalid status value'
                    }
                }), 400
        
        limit = 50
        if request.args.get('limit'):
            try:
                limit = int(request.args.get('limit'))
                if limit < 1 or limit > 100:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_LIMIT',
                        'message': 'Limit must be between 1 and 100'
                    }
                }), 400
        
        offset = 0
        if request.args.get('offset'):
            try:
                offset = int(request.args.get('offset'))
                if offset < 0:
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_OFFSET',
                        'message': 'Offset must be non-negative'
                    }
                }), 400
        
        # Get received requests
        result = MoneyRequestService.get_received_requests(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'RECEIVED_REQUESTS_ERROR',
                'message': f'Failed to get received requests: {str(e)}'
            }
        }), 500

@money_requests_bp.route('/statistics', methods=['GET'])
@auth_required
def get_request_statistics():
    """
    Get money request statistics for authenticated user
    
    Query Parameters:
        - days: Number of days to analyze (default: 30, max: 365)
    
    Returns:
        JSON with request statistics
    """
    try:
        user_id = g.current_user_id
        
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
        statistics = MoneyRequestService.get_request_statistics(user_id, days)
        
        return jsonify(statistics), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'STATISTICS_ERROR',
                'message': f'Failed to get request statistics: {str(e)}'
            }
        }), 500

@money_requests_bp.route('/validate', methods=['POST'])
@auth_required
@validate_request_data(['recipient_id', 'amount'])
def validate_request_creation():
    """
    Validate money request creation without creating it
    
    Expected JSON:
        {
            "recipient_id": "user-id",
            "amount": "50.00"
        }
    
    Returns:
        JSON with validation results
    """
    try:
        requester_id = g.current_user_id
        data = request.get_json()
        
        recipient_id = data['recipient_id']
        
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
        
        # Validate request
        validation = MoneyRequestService.validate_request_creation(
            requester_id=requester_id,
            recipient_id=recipient_id,
            amount=amount
        )
        
        return jsonify(validation), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': f'Failed to validate request: {str(e)}'
            }
        }), 500

@money_requests_bp.route('/expiring', methods=['GET'])
@auth_required
def get_expiring_requests():
    """
    Get requests that are expiring soon (admin/system endpoint)
    
    Query Parameters:
        - hours: Hours until expiration (default: 24)
    
    Returns:
        JSON with expiring requests
    """
    try:
        # Parse hours parameter
        hours = 24
        if request.args.get('hours'):
            try:
                hours = int(request.args.get('hours'))
                if hours < 1 or hours > 168:  # Max 1 week
                    raise ValueError()
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_HOURS',
                        'message': 'Hours must be between 1 and 168'
                    }
                }), 400
        
        # Get expiring requests
        expiring_requests = MoneyRequestService.get_expiring_requests(hours)
        
        return jsonify({
            'requests': [req.to_dict(include_names=True) for req in expiring_requests],
            'count': len(expiring_requests),
            'hours_threshold': hours
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'EXPIRING_REQUESTS_ERROR',
                'message': f'Failed to get expiring requests: {str(e)}'
            }
        }), 500

# Error handlers for money requests blueprint
@money_requests_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'error': {
            'code': 'BAD_REQUEST',
            'message': 'Invalid request format'
        }
    }), 400

@money_requests_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }
    }), 401

@money_requests_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Resource not found'
        }
    }), 404

@money_requests_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    db.session.rollback()
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500