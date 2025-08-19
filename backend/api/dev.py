"""
Development API endpoints for SoftBankCashWire
Only available in development mode
"""
from flask import Blueprint, jsonify, current_app
from models import User, UserRole
from sqlalchemy import or_

dev_bp = Blueprint('dev', __name__)

@dev_bp.route('/admin-user', methods=['GET'])
def get_admin_user():
    """
    Get the admin user for development mode
    Returns the admin@softbank.com user from the database
    """
    # Only allow in development mode
    if not current_app.config.get('DEBUG', False):
        return jsonify({
            'error': {
                'code': 'NOT_AVAILABLE',
                'message': 'Development endpoints not available in production'
            }
        }), 404
    
    try:
        # Find the admin user by email
        admin_user = User.query.filter(
            or_(
                User.email == 'admin@softbank.com',
                User.role == UserRole.ADMIN
            )
        ).first()
        
        if not admin_user:
            return jsonify({
                'error': {
                    'code': 'ADMIN_USER_NOT_FOUND',
                    'message': 'Admin user not found in database'
                }
            }), 404
        
        # Return user data
        user_data = {
            'id': admin_user.id,
            'microsoft_id': admin_user.microsoft_id,
            'email': admin_user.email,
            'name': admin_user.name,
            'role': admin_user.role.value,
            'account_status': admin_user.account_status.value,
            'created_at': admin_user.created_at.isoformat() if admin_user.created_at else None,
            'last_login': admin_user.last_login.isoformat() if admin_user.last_login else None,
            'permissions': ['*']  # Admin has all permissions in development
        }
        
        return jsonify({
            'user': user_data,
            'message': 'Development admin user retrieved successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'DATABASE_ERROR',
                'message': f'Failed to retrieve admin user: {str(e)}'
            }
        }), 500