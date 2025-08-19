"""
Notification API endpoints for SoftBankCashWire
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.notification_service import NotificationService
from services.auth_service import AuthService
from middleware.validation_middleware import validate_json_input, validate_query_params
from middleware.auth_middleware import auth_required

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/', methods=['GET'])
@auth_required
def get_notifications():
    """Get notifications for the current user"""
    try:
        from flask import g
        current_user_id = g.current_user_id
        
        # Get query parameters
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 notifications
        offset = int(request.args.get('offset', 0))
        
        # Get notifications
        notifications = NotificationService.get_user_notifications(
            user_id=current_user_id,
            unread_only=unread_only,
            limit=limit,
            offset=offset
        )
        
        # Convert to dict format
        notifications_data = [notification.to_dict() for notification in notifications]
        
        return jsonify({
            'notifications': notifications_data,
            'count': len(notifications_data),
            'has_more': len(notifications_data) == limit
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': {
                'code': 'INVALID_PARAMETERS',
                'message': str(e)
            }
        }), 400
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'NOTIFICATION_FETCH_FAILED',
                'message': 'Failed to fetch notifications'
            }
        }), 500


@notifications_bp.route('/unread-count', methods=['GET'])
@auth_required
def get_unread_count():
    """Get count of unread notifications for the current user"""
    try:
        from flask import g
        current_user_id = g.current_user_id
        
        count = NotificationService.get_unread_count(current_user_id)
        
        return jsonify({
            'unread_count': count
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'UNREAD_COUNT_FAILED',
                'message': 'Failed to get unread count'
            }
        }), 500


@notifications_bp.route('/<notification_id>/read', methods=['PUT'])
@auth_required
def mark_notification_as_read(notification_id):
    """Mark a specific notification as read"""
    try:
        from flask import g
        current_user_id = g.current_user_id
        
        success = NotificationService.mark_notification_as_read(
            notification_id=notification_id,
            user_id=current_user_id
        )
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'NOTIFICATION_NOT_FOUND',
                    'message': 'Notification not found'
                }
            }), 404
        
        return jsonify({
            'message': 'Notification marked as read'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'MARK_READ_FAILED',
                'message': 'Failed to mark notification as read'
            }
        }), 500


@notifications_bp.route('/mark-all-read', methods=['PUT'])
@auth_required
def mark_all_notifications_as_read():
    """Mark all notifications as read for the current user"""
    try:
        from flask import g
        current_user_id = g.current_user_id
        
        count = NotificationService.mark_all_notifications_as_read(current_user_id)
        
        return jsonify({
            'message': f'Marked {count} notifications as read',
            'count': count
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'MARK_ALL_READ_FAILED',
                'message': 'Failed to mark all notifications as read'
            }
        }), 500


@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@auth_required
def delete_notification(notification_id):
    """Delete a specific notification"""
    try:
        from flask import g
        current_user_id = g.current_user_id
        
        success = NotificationService.delete_notification(
            notification_id=notification_id,
            user_id=current_user_id
        )
        
        if not success:
            return jsonify({
                'error': {
                    'code': 'NOTIFICATION_NOT_FOUND',
                    'message': 'Notification not found'
                }
            }), 404
        
        return jsonify({
            'message': 'Notification deleted'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'DELETE_FAILED',
                'message': 'Failed to delete notification'
            }
        }), 500


@notifications_bp.route('/test', methods=['POST'])
@auth_required
@validate_json_input({
    'type': {'type': str, 'required': True},
    'title': {'type': str, 'required': True},
    'message': {'type': str, 'required': True}
})
def create_test_notification():
    """Create a test notification (for development/testing purposes)"""
    try:
        from flask import g
        current_user_id = g.current_user_id
        data = request.get_json()
        
        # Only allow in development mode
        import os
        if os.environ.get('FLASK_ENV') != 'development':
            return jsonify({
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'Test notifications only available in development mode'
                }
            }), 403
        
        from models import NotificationType, NotificationPriority
        
        # Validate notification type
        try:
            notification_type = NotificationType(data['type'])
        except ValueError:
            return jsonify({
                'error': {
                    'code': 'INVALID_TYPE',
                    'message': 'Invalid notification type'
                }
            }), 400
        
        # Get priority (default to MEDIUM)
        priority_str = data.get('priority', 'MEDIUM')
        try:
            priority = NotificationPriority(priority_str)
        except ValueError:
            priority = NotificationPriority.MEDIUM
        
        notification = NotificationService.create_notification(
            user_id=current_user_id,
            notification_type=notification_type,
            title=data['title'],
            message=data['message'],
            priority=priority,
            data=data.get('data'),
            expires_in_days=data.get('expires_in_days')
        )
        
        return jsonify({
            'message': 'Test notification created',
            'notification': notification.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'TEST_NOTIFICATION_FAILED',
                'message': 'Failed to create test notification'
            }
        }), 500


# Admin-only endpoints for system notifications

@notifications_bp.route('/broadcast', methods=['POST'])
@auth_required
@validate_json_input({
    'type': {'type': str, 'required': True},
    'title': {'type': str, 'required': True},
    'message': {'type': str, 'required': True}
})
def broadcast_notification():
    """Broadcast a notification to all users (admin only)"""
    try:
        from flask import g
        current_user_id = g.current_user_id
        
        # Check if user has admin permissions
        if not AuthService.has_permission(current_user_id, 'ADMIN'):
            return jsonify({
                'error': {
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'message': 'Admin permissions required'
                }
            }), 403
        
        data = request.get_json()
        
        from models import NotificationType, NotificationPriority
        
        # Validate notification type
        try:
            notification_type = NotificationType(data['type'])
        except ValueError:
            return jsonify({
                'error': {
                    'code': 'INVALID_TYPE',
                    'message': 'Invalid notification type'
                }
            }), 400
        
        # Get priority (default to MEDIUM)
        priority_str = data.get('priority', 'MEDIUM')
        try:
            priority = NotificationPriority(priority_str)
        except ValueError:
            priority = NotificationPriority.MEDIUM
        
        count = NotificationService.broadcast_notification_to_all_users(
            notification_type=notification_type,
            title=data['title'],
            message=data['message'],
            priority=priority,
            data=data.get('data'),
            expires_in_days=data.get('expires_in_days')
        )
        
        return jsonify({
            'message': f'Notification broadcast to {count} users',
            'recipients_count': count
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'BROADCAST_FAILED',
                'message': 'Failed to broadcast notification'
            }
        }), 500


@notifications_bp.route('/cleanup', methods=['POST'])
@auth_required
def cleanup_expired_notifications():
    """Clean up expired notifications (admin only)"""
    try:
        from flask import g
        current_user_id = g.current_user_id
        
        # Check if user has admin permissions
        if not AuthService.has_permission(current_user_id, 'ADMIN'):
            return jsonify({
                'error': {
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'message': 'Admin permissions required'
                }
            }), 403
        
        count = NotificationService.cleanup_expired_notifications()
        
        return jsonify({
            'message': f'Cleaned up {count} expired notifications',
            'deleted_count': count
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'CLEANUP_FAILED',
                'message': 'Failed to cleanup expired notifications'
            }
        }), 500


@notifications_bp.route('/stream', methods=['GET'])
@auth_required
def notification_stream():
    """Server-sent events stream for real-time notifications"""
    from flask import Response, g
    import json
    import time
    
    # Get the current user ID from the auth decorator
    current_user_id = g.current_user_id
    
    def event_stream():
        # Send initial connection confirmation
        yield f"data: {json.dumps({'type': 'connected', 'message': 'Notification stream connected'})}\n\n"
        
        # Send current unread count
        try:
            unread_count = NotificationService.get_unread_count(current_user_id)
            yield f"data: {json.dumps({'type': 'unread_count', 'count': unread_count})}\n\n"
        except Exception as e:
            print(f"Stream error: {e}")  # Debug print
            yield f"data: {json.dumps({'type': 'unread_count', 'count': 0})}\n\n"
        
        # Keep connection alive with periodic heartbeats
        last_heartbeat = time.time()
        
        while True:
            try:
                current_time = time.time()
                
                # Send heartbeat every 30 seconds
                if current_time - last_heartbeat > 30:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': current_time})}\n\n"
                    last_heartbeat = current_time
                
                # In a real implementation, you would check for new notifications
                # For now, we'll just sleep and continue the loop
                time.sleep(1)
                
            except GeneratorExit:
                # Client disconnected
                break
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Stream error occurred'})}\n\n"
                break
    
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )