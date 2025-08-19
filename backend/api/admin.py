"""
Admin API endpoints for SoftBankCashWire
Handles user management and system configuration
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from services.auth_service import AuthService
from services.audit_service import AuditService
from middleware.auth_middleware import auth_required, admin_required
from models import db, User, Account, UserRole, AccountStatus
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@admin_required
@auth_required
def get_all_users():
    """
    Get all users with filtering and pagination (Admin only)
    
    Query Parameters:
        - role: Filter by user role (EMPLOYEE, ADMIN, FINANCE)
        - status: Filter by account status (ACTIVE, SUSPENDED, CLOSED)
        - search: Search by name or email
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50, max: 200)
    
    Returns:
        JSON with user list and pagination info
    """
    try:
        # Parse query parameters
        role_filter = request.args.get('role')
        status_filter = request.args.get('status')
        search_query = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 200)
        
        # Build query
        query = User.query
        
        # Apply filters
        if role_filter:
            try:
                role = UserRole(role_filter.upper())
                query = query.filter(User.role == role)
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_ROLE',
                        'message': f'Invalid role: {role_filter}'
                    }
                }), 400
        
        if status_filter:
            try:
                status = AccountStatus(status_filter.upper())
                query = query.filter(User.account_status == status)
            except ValueError:
                return jsonify({
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': f'Invalid status: {status_filter}'
                    }
                }), 400
        
        if search_query:
            search_pattern = f'%{search_query}%'
            query = query.filter(
                db.or_(
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )
        
        # Order by name
        query = query.order_by(User.name)
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Format users with account info
        users_data = []
        for user in pagination.items:
            account = Account.query.filter_by(user_id=user.id).first()
            user_data = user.to_dict()
            user_data['account'] = {
                'balance': str(account.balance) if account else '0.00',
                'created_at': account.created_at.isoformat() if account else None
            }
            users_data.append(user_data)
        
        # Log admin action
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='ADMIN_USERS_VIEWED',
            entity_type='UserManagement',
            new_values={
                'filters': {
                    'role': role_filter,
                    'status': status_filter,
                    'search': search_query
                },
                'page': page,
                'per_page': per_page,
                'total_results': pagination.total
            }
        )
        
        return jsonify({
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'INVALID_PARAMETERS',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'error': {
                'code': 'USERS_FETCH_ERROR',
                'message': 'Failed to fetch users'
            }
        }), 500

@admin_bp.route('/users/<user_id>', methods=['GET'])
@admin_required
@auth_required
def get_user_details(user_id):
    """
    Get detailed user information (Admin only)
    
    Returns:
        JSON with user details, account info, and recent activity
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Get account info
        account = Account.query.filter_by(user_id=user_id).first()
        
        # Get recent transactions (last 30 days)
        from models import Transaction
        recent_transactions = Transaction.query.filter(
            db.or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            ),
            Transaction.created_at >= datetime.now(datetime.UTC) - timedelta(days=30)
        ).order_by(Transaction.created_at.desc()).limit(10).all()
        
        # Get recent audit logs (last 30 days)
        recent_audit_logs = AuditService.get_user_audit_logs(
            user_id, 
            start_date=datetime.now(datetime.UTC) - timedelta(days=30),
            limit=10
        )
        
        user_details = {
            'user': user.to_dict(),
            'account': {
                'balance': str(account.balance) if account else '0.00',
                'created_at': account.created_at.isoformat() if account else None,
                'updated_at': account.updated_at.isoformat() if account else None
            },
            'recent_transactions': [
                {
                    'id': t.id,
                    'amount': str(t.amount),
                    'type': 'sent' if t.sender_id == user_id else 'received',
                    'other_party': t.recipient.name if t.sender_id == user_id else t.sender.name,
                    'created_at': t.created_at.isoformat(),
                    'status': t.status.value
                } for t in recent_transactions
            ],
            'recent_activity': recent_audit_logs.get('audit_logs', [])[:10]
        }
        
        # Log admin action
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='ADMIN_USER_DETAILS_VIEWED',
            entity_type='UserManagement',
            entity_id=user_id,
            new_values={
                'viewed_user': user.name,
                'viewed_user_email': user.email
            }
        )
        
        return jsonify(user_details), 200
        
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        return jsonify({
            'error': {
                'code': 'USER_DETAILS_ERROR',
                'message': 'Failed to get user details'
            }
        }), 500

@admin_bp.route('/users/<user_id>/status', methods=['PUT'])
@admin_required
@auth_required
def update_user_status(user_id):
    """
    Update user account status (Admin only)
    
    Expected JSON:
        {
            "status": "ACTIVE" | "SUSPENDED" | "CLOSED",
            "reason": "Optional reason for status change"
        }
    
    Returns:
        JSON with updated user info
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
        
        new_status = data.get('status')
        reason = data.get('reason', '')
        
        if not new_status:
            return jsonify({
                'error': {
                    'code': 'MISSING_STATUS',
                    'message': 'Status is required'
                }
            }), 400
        
        # Validate status
        try:
            status_enum = AccountStatus(new_status.upper())
        except ValueError:
            return jsonify({
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': f'Invalid status: {new_status}'
                }
            }), 400
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Prevent admin from deactivating themselves
        if user_id == g.current_user_id and status_enum != AccountStatus.ACTIVE:
            return jsonify({
                'error': {
                    'code': 'CANNOT_DEACTIVATE_SELF',
                    'message': 'Cannot deactivate your own account'
                }
            }), 400
        
        # Store old status for audit
        old_status = user.account_status
        
        # Update status
        user.account_status = status_enum
        db.session.commit()
        
        # Log admin action
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='ADMIN_USER_STATUS_CHANGED',
            entity_type='User',
            entity_id=user_id,
            old_values={
                'account_status': old_status.value if old_status else None
            },
            new_values={
                'account_status': status_enum.value,
                'reason': reason,
                'changed_by': g.current_user.name if g.current_user else 'Unknown',
                'target_user': user.name
            }
        )
        
        return jsonify({
            'message': f'User status updated to {status_enum.value}',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user status: {str(e)}")
        return jsonify({
            'error': {
                'code': 'STATUS_UPDATE_ERROR',
                'message': 'Failed to update user status'
            }
        }), 500

@admin_bp.route('/users/<user_id>/role', methods=['PUT'])
@admin_required
@auth_required
def update_user_role(user_id):
    """
    Update user role (Admin only)
    
    Expected JSON:
        {
            "role": "EMPLOYEE" | "ADMIN" | "FINANCE",
            "reason": "Optional reason for role change"
        }
    
    Returns:
        JSON with updated user info
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
        
        new_role = data.get('role')
        reason = data.get('reason', '')
        
        if not new_role:
            return jsonify({
                'error': {
                    'code': 'MISSING_ROLE',
                    'message': 'Role is required'
                }
            }), 400
        
        # Validate role
        try:
            role_enum = UserRole(new_role.upper())
        except ValueError:
            return jsonify({
                'error': {
                    'code': 'INVALID_ROLE',
                    'message': f'Invalid role: {new_role}'
                }
            }), 400
        
        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Prevent admin from removing their own admin role if they're the only admin
        if user_id == g.current_user_id and role_enum != UserRole.ADMIN:
            admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
            if admin_count <= 1:
                return jsonify({
                    'error': {
                        'code': 'CANNOT_REMOVE_LAST_ADMIN',
                        'message': 'Cannot remove admin role from the last admin user'
                    }
                }), 400
        
        # Store old role for audit
        old_role = user.role
        
        # Update role
        user.role = role_enum
        db.session.commit()
        
        # Log admin action
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='ADMIN_USER_ROLE_CHANGED',
            entity_type='User',
            entity_id=user_id,
            old_values={
                'role': old_role.value if old_role else None
            },
            new_values={
                'role': role_enum.value,
                'reason': reason,
                'changed_by': g.current_user.name if g.current_user else 'Unknown',
                'target_user': user.name
            }
        )
        
        return jsonify({
            'message': f'User role updated to {role_enum.value}',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user role: {str(e)}")
        return jsonify({
            'error': {
                'code': 'ROLE_UPDATE_ERROR',
                'message': 'Failed to update user role'
            }
        }), 500

@admin_bp.route('/system/config', methods=['GET'])
@admin_required
@auth_required
def get_system_config():
    """
    Get system configuration (Admin only)
    
    Returns:
        JSON with system configuration
    """
    try:
        import os
        
        config = {
            'application': {
                'name': 'SoftBankCashWire',
                'version': '1.0.0',
                'environment': os.environ.get('FLASK_ENV', 'production')
            },
            'features': {
                'microsoft_sso_enabled': bool(os.environ.get('MICROSOFT_CLIENT_ID')),
                'audit_logging_enabled': True,
                'reporting_enabled': True,
                'rate_limiting_enabled': True
            },
            'limits': {
                'max_account_balance': '250.00',
                'min_account_balance': '-250.00',
                'max_transaction_amount': '500.00',
                'session_timeout_hours': 8
            },
            'security': {
                'password_policy_enabled': False,  # Using SSO
                'two_factor_enabled': False,  # Using Microsoft SSO
                'audit_retention_days': 2555,  # 7 years
                'session_encryption': True
            }
        }
        
        # Log admin action
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='ADMIN_CONFIG_VIEWED',
            entity_type='SystemConfiguration'
        )
        
        return jsonify(config), 200
        
    except Exception as e:
        logger.error(f"Error getting system config: {str(e)}")
        return jsonify({
            'error': {
                'code': 'CONFIG_ERROR',
                'message': 'Failed to get system configuration'
            }
        }), 500

@admin_bp.route('/system/maintenance', methods=['POST'])
@admin_required
@auth_required
def system_maintenance():
    """
    Perform system maintenance tasks (Admin only)
    
    Expected JSON:
        {
            "task": "cleanup_sessions" | "optimize_database" | "verify_integrity",
            "parameters": {}  // Optional task-specific parameters
        }
    
    Returns:
        JSON with maintenance results
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
        
        task = data.get('task')
        parameters = data.get('parameters', {})
        
        if not task:
            return jsonify({
                'error': {
                    'code': 'MISSING_TASK',
                    'message': 'Task is required'
                }
            }), 400
        
        result = {'task': task, 'success': False, 'message': '', 'details': {}}
        
        if task == 'cleanup_sessions':
            # Clean up expired sessions
            from services.auth_service import AuthService
            cleanup_result = AuthService.cleanup_expired_sessions()
            result.update({
                'success': True,
                'message': f'Cleaned up {cleanup_result["cleaned_count"]} expired sessions',
                'details': cleanup_result
            })
        
        elif task == 'optimize_database':
            # Optimize database (SQLite VACUUM)
            try:
                db.session.execute('VACUUM')
                db.session.commit()
                result.update({
                    'success': True,
                    'message': 'Database optimization completed',
                    'details': {'operation': 'VACUUM'}
                })
            except Exception as e:
                result.update({
                    'success': False,
                    'message': f'Database optimization failed: {str(e)}'
                })
        
        elif task == 'verify_integrity':
            # Verify audit log integrity
            integrity_result = AuditService.verify_audit_integrity()
            result.update({
                'success': integrity_result['overall_status'] == 'HEALTHY',
                'message': f'Integrity check completed: {integrity_result["overall_status"]}',
                'details': integrity_result
            })
        
        else:
            return jsonify({
                'error': {
                    'code': 'INVALID_TASK',
                    'message': f'Unknown maintenance task: {task}'
                }
            }), 400
        
        # Log maintenance action
        AuditService.log_user_action(
            user_id=g.current_user_id,
            action_type='ADMIN_MAINTENANCE_PERFORMED',
            entity_type='SystemMaintenance',
            new_values={
                'task': task,
                'parameters': parameters,
                'success': result['success'],
                'performed_by': g.current_user.name if g.current_user else 'Unknown'
            }
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error performing maintenance: {str(e)}")
        return jsonify({
            'error': {
                'code': 'MAINTENANCE_ERROR',
                'message': 'Failed to perform maintenance task'
            }
        }), 500

# Error handlers for admin blueprint
@admin_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        'error': {
            'code': 'BAD_REQUEST',
            'message': 'Invalid request format'
        }
    }), 400

@admin_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        'error': {
            'code': 'UNAUTHORIZED',
            'message': 'Authentication required'
        }
    }), 401

@admin_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    return jsonify({
        'error': {
            'code': 'FORBIDDEN',
            'message': 'Admin access required'
        }
    }), 403

@admin_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    db.session.rollback()
    return jsonify({
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500