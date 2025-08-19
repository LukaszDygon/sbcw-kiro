"""
Transaction API endpoints for SoftBankCashWire
"""
from flask import Blueprint, request, jsonify, g
from decimal import Decimal, InvalidOperation
from services.transaction_service import TransactionService
from middleware.auth_middleware import auth_required, get_client_info, validate_request_data
from models import db, TransactionType

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/send', methods=['POST'])
@auth_required
@validate_request_data(['recipient_id', 'amount'])
def send_money():
    """
    Send money to another user
    
    Expected JSON:
        {
            "recipient_id": "user-id",
            "amount": "50.00",
            "category": "Lunch",  // Optional
            "note": "Lunch payment"  // Optional
        }
    
    Returns:
        JSON with transaction result
    """
    try:
        sender_id = g.current_user_id
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
        
        category = data.get('category')
        note = data.get('note')
        
        # Validate note length
        if note and len(note) > 500:
            return jsonify({
                'error': {
                    'code': 'NOTE_TOO_LONG',
                    'message': 'Note cannot exceed 500 characters'
                }
            }), 400
        
        # Validate category length
        if category and len(category) > 100:
            return jsonify({
                'error': {
                    'code': 'CATEGORY_TOO_LONG',
                    'message': 'Category cannot exceed 100 characters'
                }
            }), 400
        
        ip_address, user_agent = get_client_info()
        
        # Process transaction
        result = TransactionService.send_money(
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=amount,
            category=category,
            note=note,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'TRANSACTION_FAILED',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'SEND_MONEY_ERROR',
                'message': f'Failed to send money: {str(e)}'
            }
        }), 500

@transactions_bp.route('/send-bulk', methods=['POST'])
@auth_required
@validate_request_data(['recipients'])
def send_bulk_money():
    """
    Send money to multiple recipients
    
    Expected JSON:
        {
            "recipients": [
                {
                    "recipient_id": "user-id-1",
                    "amount": "25.00",
                    "category": "Lunch",  // Optional
                    "note": "Lunch split"  // Optional
                },
                {
                    "recipient_id": "user-id-2",
                    "amount": "30.00",
                    "category": "Lunch",
                    "note": "Lunch split"
                }
            ]
        }
    
    Returns:
        JSON with bulk transaction results
    """
    try:
        sender_id = g.current_user_id
        data = request.get_json()
        
        recipients = data['recipients']
        
        if not isinstance(recipients, list):
            return jsonify({
                'error': {
                    'code': 'INVALID_RECIPIENTS',
                    'message': 'Recipients must be a list'
                }
            }), 400
        
        # Validate each recipient
        for i, recipient in enumerate(recipients):
            if not isinstance(recipient, dict):
                return jsonify({
                    'error': {
                        'code': 'INVALID_RECIPIENT_FORMAT',
                        'message': f'Recipient {i+1} must be an object'
                    }
                }), 400
            
            if 'recipient_id' not in recipient or 'amount' not in recipient:
                return jsonify({
                    'error': {
                        'code': 'MISSING_RECIPIENT_FIELDS',
                        'message': f'Recipient {i+1} missing required fields (recipient_id, amount)'
                    }
                }), 400
            
            # Validate amount
            try:
                Decimal(str(recipient['amount']))
            except (InvalidOperation, ValueError):
                return jsonify({
                    'error': {
                        'code': 'INVALID_RECIPIENT_AMOUNT',
                        'message': f'Recipient {i+1} amount must be a valid number'
                    }
                }), 400
            
            # Validate note length
            if recipient.get('note') and len(recipient['note']) > 500:
                return jsonify({
                    'error': {
                        'code': 'RECIPIENT_NOTE_TOO_LONG',
                        'message': f'Recipient {i+1} note cannot exceed 500 characters'
                    }
                }), 400
            
            # Validate category length
            if recipient.get('category') and len(recipient['category']) > 100:
                return jsonify({
                    'error': {
                        'code': 'RECIPIENT_CATEGORY_TOO_LONG',
                        'message': f'Recipient {i+1} category cannot exceed 100 characters'
                    }
                }), 400
        
        ip_address, user_agent = get_client_info()
        
        # Process bulk transaction
        result = TransactionService.send_bulk_money(
            sender_id=sender_id,
            recipients=recipients,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'BULK_TRANSACTION_FAILED',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BULK_SEND_ERROR',
                'message': f'Failed to send bulk money: {str(e)}'
            }
        }), 500

@transactions_bp.route('/validate', methods=['POST'])
@auth_required
@validate_request_data(['amount'])
def validate_transaction():
    """
    Validate a transaction before processing
    
    Expected JSON:
        {
            "recipient_id": "user-id",  // Optional for general validation
            "amount": "50.00",
            "transaction_type": "TRANSFER"  // Optional
        }
    
    Returns:
        JSON with validation results
    """
    try:
        sender_id = g.current_user_id
        data = request.get_json()
        
        recipient_id = data.get('recipient_id')
        
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
        
        # Parse transaction type
        transaction_type = None
        if data.get('transaction_type'):
            try:
                transaction_type = TransactionType(data['transaction_type'])
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_TRANSACTION_TYPE',
                        'message': 'Invalid transaction type'
                    }
                }), 400
        
        # Validate transaction
        validation = TransactionService.validate_transaction(
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=amount,
            transaction_type=transaction_type
        )
        
        return jsonify(validation), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': f'Failed to validate transaction: {str(e)}'
            }
        }), 500

@transactions_bp.route('/<transaction_id>', methods=['GET'])
@auth_required
def get_transaction(transaction_id):
    """
    Get transaction details by ID
    
    Returns:
        JSON with transaction details
    """
    try:
        user_id = g.current_user_id
        
        transaction = TransactionService.get_transaction_by_id(transaction_id, user_id)
        
        if not transaction:
            return jsonify({
                'error': {
                    'code': 'TRANSACTION_NOT_FOUND',
                    'message': 'Transaction not found or access denied'
                }
            }), 404
        
        return jsonify({
            'transaction': transaction.to_dict(include_names=True)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'GET_TRANSACTION_ERROR',
                'message': f'Failed to get transaction: {str(e)}'
            }
        }), 500

@transactions_bp.route('/recent', methods=['GET'])
@auth_required
def get_recent_transactions():
    """
    Get recent transactions for authenticated user
    
    Query Parameters:
        - limit: Number of transactions to return (default: 10, max: 50)
    
    Returns:
        JSON with recent transactions
    """
    try:
        user_id = g.current_user_id
        
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
        
        # Get recent transactions
        transactions = TransactionService.get_recent_transactions(user_id, limit)
        
        return jsonify({
            'transactions': [t.to_dict(include_names=True) for t in transactions],
            'count': len(transactions)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'RECENT_TRANSACTIONS_ERROR',
                'message': f'Failed to get recent transactions: {str(e)}'
            }
        }), 500

@transactions_bp.route('/statistics', methods=['GET'])
@auth_required
def get_transaction_statistics():
    """
    Get transaction statistics for authenticated user
    
    Query Parameters:
        - days: Number of days to analyze (default: 30, max: 365)
    
    Returns:
        JSON with transaction statistics
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
        statistics = TransactionService.get_transaction_statistics(user_id, days)
        
        return jsonify(statistics), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'STATISTICS_ERROR',
                'message': f'Failed to get transaction statistics: {str(e)}'
            }
        }), 500

@transactions_bp.route('/<transaction_id>/cancel', methods=['POST'])
@auth_required
def cancel_transaction(transaction_id):
    """
    Cancel a transaction (if possible)
    
    Returns:
        JSON with cancellation result
    """
    try:
        user_id = g.current_user_id
        ip_address, user_agent = get_client_info()
        
        result = TransactionService.cancel_transaction(
            transaction_id=transaction_id,
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
                'message': f'Failed to cancel transaction: {str(e)}'
            }
        }), 500

@transactions_bp.route('/categories', methods=['GET'])
@auth_required
def get_transaction_categories():
    """
    Get list of available transaction categories
    
    Returns:
        JSON with category list
    """
    try:
        categories = [
            {
                'id': 'lunch-meals',
                'name': 'Lunch & Meals',
                'description': 'Food-related expenses and shared meals'
            },
            {
                'id': 'office-supplies',
                'name': 'Office Supplies',
                'description': 'Shared office equipment and supplies'
            },
            {
                'id': 'transportation',
                'name': 'Transportation',
                'description': 'Travel expenses and ride sharing'
            },
            {
                'id': 'entertainment',
                'name': 'Entertainment',
                'description': 'Team activities and social events'
            },
            {
                'id': 'event-contribution',
                'name': 'Event Contribution',
                'description': 'Contributions to event accounts'
            },
            {
                'id': 'miscellaneous',
                'name': 'Miscellaneous',
                'description': 'General transactions'
            }
        ]
        
        return jsonify({
            'categories': categories
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CATEGORIES_ERROR',
                'message': f'Failed to get categories: {str(e)}'
            }
        }), 500

# Error handlers for transactions blueprint
@transactions_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'error': {
            'code': 'BAD_REQUEST',
            'message': 'Invalid request format'
        }
    }), 400

@transactions_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }
    }), 401

@transactions_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Resource not found'
        }
    }), 404

@transactions_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    db.session.rollback()
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500