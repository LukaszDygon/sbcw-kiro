"""
Events API endpoints for SoftBankCashWire
"""
from flask import Blueprint, request, jsonify, g
from decimal import Decimal, InvalidOperation
from datetime import datetime
from services.event_service import EventService
from middleware.auth_middleware import auth_required, get_client_info, validate_request_data
from models import db, EventStatus

events_bp = Blueprint('events', __name__)

@events_bp.route('/create', methods=['POST'])
@auth_required
@validate_request_data(['name', 'description'])
def create_event():
    """
    Create a new event account
    
    Expected JSON:
        {
            "name": "Team Lunch",
            "description": "Monthly team lunch event",
            "target_amount": "200.00",  // Optional
            "deadline": "2024-12-31T23:59:59Z"  // Optional, ISO format
        }
    
    Returns:
        JSON with event creation result
    """
    try:
        creator_id = g.current_user_id
        data = request.get_json()
        
        # Validate name and description lengths
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if len(name) > 255:
            return jsonify({
                'error': {
                    'code': 'NAME_TOO_LONG',
                    'message': 'Event name cannot exceed 255 characters'
                }
            }), 400
        
        if len(description) > 1000:
            return jsonify({
                'error': {
                    'code': 'DESCRIPTION_TOO_LONG',
                    'message': 'Event description cannot exceed 1000 characters'
                }
            }), 400
        
        # Validate target amount if provided
        if data.get('target_amount'):
            try:
                target_amount = Decimal(str(data['target_amount']))
                if target_amount <= 0:
                    return jsonify({
                        'error': {
                            'code': 'INVALID_TARGET_AMOUNT',
                            'message': 'Target amount must be positive'
                        }
                    }), 400
                data['target_amount'] = target_amount
            except (InvalidOperation, ValueError):
                return jsonify({
                    'error': {
                        'code': 'INVALID_TARGET_AMOUNT',
                        'message': 'Target amount must be a valid number'
                    }
                }), 400
        
        # Validate deadline if provided
        if data.get('deadline'):
            try:
                deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
                if deadline <= datetime.utcnow():
                    return jsonify({
                        'error': {
                            'code': 'INVALID_DEADLINE',
                            'message': 'Deadline must be in the future'
                        }
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'error': {
                        'code': 'INVALID_DEADLINE',
                        'message': 'Deadline must be a valid ISO format date'
                    }
                }), 400
        
        ip_address, user_agent = get_client_info()
        
        # Create event
        result = EventService.create_event_account(
            creator_id=creator_id,
            event_data=data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(result), 201
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'EVENT_CREATION_FAILED',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CREATE_EVENT_ERROR',
                'message': f'Failed to create event: {str(e)}'
            }
        }), 500

@events_bp.route('/<event_id>/contribute', methods=['POST'])
@auth_required
@validate_request_data(['amount'])
def contribute_to_event(event_id):
    """
    Contribute money to an event account
    
    Expected JSON:
        {
            "amount": "25.00",
            "note": "Happy to contribute!"  // Optional
        }
    
    Returns:
        JSON with contribution result
    """
    try:
        user_id = g.current_user_id
        data = request.get_json()
        
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
        
        if amount <= 0:
            return jsonify({
                'error': {
                    'code': 'INVALID_AMOUNT',
                    'message': 'Amount must be positive'
                }
            }), 400
        
        note = data.get('note')
        
        # Validate note length
        if note and len(note) > 500:
            return jsonify({
                'error': {
                    'code': 'NOTE_TOO_LONG',
                    'message': 'Note cannot exceed 500 characters'
                }
            }), 400
        
        ip_address, user_agent = get_client_info()
        
        # Process contribution
        result = EventService.contribute_to_event(
            user_id=user_id,
            event_id=event_id,
            amount=amount,
            note=note,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'CONTRIBUTION_FAILED',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CONTRIBUTE_ERROR',
                'message': f'Failed to process contribution: {str(e)}'
            }
        }), 500

@events_bp.route('/<event_id>/close', methods=['POST'])
@auth_required
def close_event(event_id):
    """
    Close an event account
    
    Returns:
        JSON with closure result
    """
    try:
        user_id = g.current_user_id
        ip_address, user_agent = get_client_info()
        
        result = EventService.close_event_account(
            event_id=event_id,
            closer_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'CLOSE_FAILED',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CLOSE_ERROR',
                'message': f'Failed to close event: {str(e)}'
            }
        }), 500

@events_bp.route('/<event_id>/cancel', methods=['POST'])
@auth_required
def cancel_event(event_id):
    """
    Cancel an event account
    
    Returns:
        JSON with cancellation result
    """
    try:
        user_id = g.current_user_id
        ip_address, user_agent = get_client_info()
        
        result = EventService.cancel_event_account(
            event_id=event_id,
            canceller_id=user_id,
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
                'message': f'Failed to cancel event: {str(e)}'
            }
        }), 500

@events_bp.route('/<event_id>', methods=['GET'])
@auth_required
def get_event(event_id):
    """
    Get event details by ID
    
    Query Parameters:
        - include_contributions: Include contribution details (true/false)
    
    Returns:
        JSON with event details
    """
    try:
        include_contributions = request.args.get('include_contributions', 'false').lower() == 'true'
        
        event = EventService.get_event_by_id(event_id, include_contributions)
        
        if not event:
            return jsonify({
                'error': {
                    'code': 'EVENT_NOT_FOUND',
                    'message': 'Event not found'
                }
            }), 404
        
        event_data = event.to_dict(include_creator_name=True, include_contributions=include_contributions)
        
        return jsonify({
            'event': event_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'GET_EVENT_ERROR',
                'message': f'Failed to get event: {str(e)}'
            }
        }), 500

@events_bp.route('/<event_id>/contributions', methods=['GET'])
@auth_required
def get_event_contributions(event_id):
    """
    Get contributions for a specific event
    
    Returns:
        JSON with event contributions
    """
    try:
        # Verify event exists
        event = EventService.get_event_by_id(event_id)
        if not event:
            return jsonify({
                'error': {
                    'code': 'EVENT_NOT_FOUND',
                    'message': 'Event not found'
                }
            }), 404
        
        contributions = EventService.get_event_contributions(event_id)
        
        return jsonify({
            'event_id': event_id,
            'event_name': event.name,
            'contributions': contributions,
            'total_contributions': str(event.total_contributions),
            'contributor_count': event.get_contributor_count()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'GET_CONTRIBUTIONS_ERROR',
                'message': f'Failed to get contributions: {str(e)}'
            }
        }), 500

@events_bp.route('/active', methods=['GET'])
@auth_required
def get_active_events():
    """
    Get active event accounts
    
    Query Parameters:
        - limit: Number of events to return (default: 50, max: 100)
        - offset: Number of events to skip (default: 0)
    
    Returns:
        JSON with active events and pagination
    """
    try:
        # Parse query parameters
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
        
        # Get active events
        result = EventService.get_active_events(limit=limit, offset=offset)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'GET_ACTIVE_EVENTS_ERROR',
                'message': f'Failed to get active events: {str(e)}'
            }
        }), 500

@events_bp.route('/my-events', methods=['GET'])
@auth_required
def get_my_events():
    """
    Get events created by authenticated user
    
    Query Parameters:
        - status: Filter by status (ACTIVE, CLOSED, CANCELLED)
        - limit: Number of events to return (default: 50, max: 100)
        - offset: Number of events to skip (default: 0)
    
    Returns:
        JSON with user's events and pagination
    """
    try:
        user_id = g.current_user_id
        
        # Parse query parameters
        status = None
        if request.args.get('status'):
            try:
                status = EventStatus(request.args.get('status'))
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
        
        # Get user's events
        result = EventService.get_events_by_creator(
            creator_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'GET_MY_EVENTS_ERROR',
                'message': f'Failed to get your events: {str(e)}'
            }
        }), 500

@events_bp.route('/my-contributions', methods=['GET'])
@auth_required
def get_my_contributions():
    """
    Get contributions made by authenticated user
    
    Query Parameters:
        - limit: Number of contributions to return (default: 50, max: 100)
        - offset: Number of contributions to skip (default: 0)
    
    Returns:
        JSON with user's contributions and pagination
    """
    try:
        user_id = g.current_user_id
        
        # Parse query parameters
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
        
        # Get user's contributions
        result = EventService.get_user_contributions(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'GET_MY_CONTRIBUTIONS_ERROR',
                'message': f'Failed to get your contributions: {str(e)}'
            }
        }), 500

@events_bp.route('/search', methods=['GET'])
@auth_required
def search_events():
    """
    Search events by name or description
    
    Query Parameters:
        - q: Search term (required)
        - status: Filter by status (ACTIVE, CLOSED, CANCELLED)
        - limit: Number of events to return (default: 50, max: 100)
        - offset: Number of events to skip (default: 0)
    
    Returns:
        JSON with matching events and pagination
    """
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return jsonify({
                'error': {
                    'code': 'MISSING_SEARCH_TERM',
                    'message': 'Search term is required'
                }
            }), 400
        
        if len(search_term) < 2:
            return jsonify({
                'error': {
                    'code': 'SEARCH_TERM_TOO_SHORT',
                    'message': 'Search term must be at least 2 characters'
                }
            }), 400
        
        # Parse other query parameters
        status = None
        if request.args.get('status'):
            try:
                status = EventStatus(request.args.get('status'))
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
        
        # Search events
        result = EventService.search_events(
            search_term=search_term,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'SEARCH_ERROR',
                'message': f'Failed to search events: {str(e)}'
            }
        }), 500

@events_bp.route('/statistics', methods=['GET'])
@auth_required
def get_event_statistics():
    """
    Get event statistics
    
    Query Parameters:
        - days: Number of days to analyze (default: 30, max: 365)
    
    Returns:
        JSON with event statistics
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
        statistics = EventService.get_event_statistics(days)
        
        return jsonify(statistics), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'STATISTICS_ERROR',
                'message': f'Failed to get event statistics: {str(e)}'
            }
        }), 500

@events_bp.route('/validate', methods=['POST'])
@auth_required
@validate_request_data(['name', 'description'])
def validate_event_creation():
    """
    Validate event creation without creating it
    
    Expected JSON:
        {
            "name": "Event Name",
            "description": "Event Description",
            "target_amount": "200.00",  // Optional
            "deadline": "2024-12-31T23:59:59Z"  // Optional
        }
    
    Returns:
        JSON with validation results
    """
    try:
        creator_id = g.current_user_id
        data = request.get_json()
        
        # Validate event data
        validation = EventService.validate_event_creation(creator_id, data)
        
        return jsonify(validation), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': f'Failed to validate event: {str(e)}'
            }
        }), 500

# Error handlers for events blueprint
@events_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'error': {
            'code': 'BAD_REQUEST',
            'message': 'Invalid request format'
        }
    }), 400

@events_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }
    }), 401

@events_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Resource not found'
        }
    }), 404

@events_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    db.session.rollback()
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500