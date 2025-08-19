"""
Backup and data management API endpoints for SoftBankCashWire
Handles backup operations, data retention, and recovery procedures
"""
from flask import Blueprint, request, jsonify, make_response
from datetime import datetime, timedelta
from functools import wraps
from services.backup_service import BackupService
from services.data_retention_service import DataRetentionService
from services.scheduler_service import scheduler_service
from services.auth_service import AuthService
from models import UserRole
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

backup_bp = Blueprint('backup', __name__, url_prefix='/api/backup')

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

def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(current_user, *args, **kwargs):
        if current_user.role not in [UserRole.ADMIN, UserRole.FINANCE]:
            return jsonify({'error': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated_function

@backup_bp.route('/create', methods=['POST'])
@require_auth
@require_admin
def create_backup(current_user):
    """
    Create a database backup
    
    Request body:
        backup_name (str, optional): Custom backup name
    
    Returns:
        JSON response with backup information
    """
    try:
        data = request.get_json() or {}
        backup_name = data.get('backup_name')
        
        result = BackupService.create_database_backup(backup_name)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Backup created successfully',
                'backup_info': result['backup_info']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create backup'
        }), 500

@backup_bp.route('/list', methods=['GET'])
@require_auth
@require_admin
def list_backups(current_user):
    """
    List all available backups
    
    Returns:
        JSON response with backup list
    """
    try:
        backups = BackupService.list_backups()
        
        return jsonify({
            'success': True,
            'backups': backups,
            'total_count': len(backups)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to list backups'
        }), 500

@backup_bp.route('/restore', methods=['POST'])
@require_auth
@require_admin
def restore_backup(current_user):
    """
    Restore database from backup
    
    Request body:
        backup_id (str): Backup ID to restore
        target_path (str, optional): Target path for restored database
    
    Returns:
        JSON response with restoration information
    """
    try:
        data = request.get_json()
        
        if not data or 'backup_id' not in data:
            return jsonify({
                'success': False,
                'error': 'backup_id is required'
            }), 400
        
        backup_id = data['backup_id']
        target_path = data.get('target_path')
        
        result = BackupService.restore_database_backup(backup_id, target_path)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Database restored successfully',
                'restoration_info': {
                    'restored_path': result['restored_path'],
                    'backup_metadata': result['backup_metadata'],
                    'tables_count': result['tables_count']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to restore backup'
        }), 500

@backup_bp.route('/verify/<backup_id>', methods=['GET'])
@require_auth
@require_admin
def verify_backup(current_user, backup_id):
    """
    Verify backup integrity
    
    Args:
        backup_id: Backup ID to verify
    
    Returns:
        JSON response with verification results
    """
    try:
        result = BackupService.verify_backup_integrity(backup_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Backup verification completed',
                'verification_info': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error verifying backup: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to verify backup'
        }), 500

@backup_bp.route('/cleanup', methods=['POST'])
@require_auth
@require_admin
def cleanup_backups(current_user):
    """
    Clean up old backups based on retention policy
    
    Returns:
        JSON response with cleanup results
    """
    try:
        result = BackupService.cleanup_old_backups()
        
        return jsonify({
            'success': True,
            'message': 'Backup cleanup completed',
            'cleanup_info': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up backups: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to cleanup backups'
        }), 500

@backup_bp.route('/statistics', methods=['GET'])
@require_auth
@require_admin
def get_backup_statistics(current_user):
    """
    Get backup system statistics
    
    Returns:
        JSON response with backup statistics
    """
    try:
        stats = BackupService.get_backup_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting backup statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get backup statistics'
        }), 500

@backup_bp.route('/retention/policies', methods=['GET'])
@require_auth
@require_admin
def get_retention_policies(current_user):
    """
    Get current data retention policies
    
    Returns:
        JSON response with retention policies
    """
    try:
        policies = DataRetentionService.get_retention_policies()
        
        return jsonify({
            'success': True,
            'policies': policies
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting retention policies: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get retention policies'
        }), 500

@backup_bp.route('/retention/policies', methods=['PUT'])
@require_auth
@require_admin
def update_retention_policy(current_user):
    """
    Update data retention policy
    
    Request body:
        policy_name (str): Name of the retention policy
        retention_days (int): Number of days to retain data
    
    Returns:
        JSON response with update result
    """
    try:
        data = request.get_json()
        
        if not data or 'policy_name' not in data or 'retention_days' not in data:
            return jsonify({
                'success': False,
                'error': 'policy_name and retention_days are required'
            }), 400
        
        policy_name = data['policy_name']
        retention_days = data['retention_days']
        
        result = DataRetentionService.update_retention_policy(policy_name, retention_days)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Retention policy updated successfully',
                'update_info': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error updating retention policy: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update retention policy'
        }), 500

@backup_bp.route('/retention/status', methods=['GET'])
@require_auth
@require_admin
def get_retention_status(current_user):
    """
    Get current data retention status
    
    Returns:
        JSON response with retention status
    """
    try:
        result = DataRetentionService.get_data_retention_status()
        
        if result['success']:
            return jsonify({
                'success': True,
                'retention_status': result['status']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting retention status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get retention status'
        }), 500

@backup_bp.route('/retention/cleanup', methods=['POST'])
@require_auth
@require_admin
def run_data_cleanup(current_user):
    """
    Run full data cleanup based on retention policies
    
    Returns:
        JSON response with cleanup results
    """
    try:
        result = DataRetentionService.run_full_cleanup()
        
        return jsonify({
            'success': True,
            'message': 'Data cleanup completed',
            'cleanup_results': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error running data cleanup: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to run data cleanup'
        }), 500

@backup_bp.route('/retention/compliance', methods=['GET'])
@require_auth
@require_admin
def validate_compliance(current_user):
    """
    Validate data retention compliance
    
    Returns:
        JSON response with compliance validation results
    """
    try:
        result = DataRetentionService.validate_retention_compliance()
        
        if result['success']:
            return jsonify({
                'success': True,
                'compliance': result['compliance']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error validating compliance: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate compliance'
        }), 500

@backup_bp.route('/scheduler/status', methods=['GET'])
@require_auth
@require_admin
def get_scheduler_status(current_user):
    """
    Get automated scheduler status
    
    Returns:
        JSON response with scheduler status
    """
    try:
        result = scheduler_service.get_scheduler_status()
        
        if result['success']:
            return jsonify({
                'success': True,
                'scheduler_status': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get scheduler status'
        }), 500

@backup_bp.route('/scheduler/start', methods=['POST'])
@require_auth
@require_admin
def start_scheduler(current_user):
    """
    Start the automated scheduler
    
    Returns:
        JSON response with start result
    """
    try:
        result = scheduler_service.start_scheduler()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Scheduler started successfully',
                'scheduler_info': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to start scheduler'
        }), 500

@backup_bp.route('/scheduler/stop', methods=['POST'])
@require_auth
@require_admin
def stop_scheduler(current_user):
    """
    Stop the automated scheduler
    
    Returns:
        JSON response with stop result
    """
    try:
        result = scheduler_service.stop_scheduler()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Scheduler stopped successfully',
                'scheduler_info': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to stop scheduler'
        }), 500

@backup_bp.route('/scheduler/run/<job_id>', methods=['POST'])
@require_auth
@require_admin
def run_scheduled_job(current_user, job_id):
    """
    Manually run a scheduled job
    
    Args:
        job_id: ID of the job to run
    
    Returns:
        JSON response with execution result
    """
    try:
        result = scheduler_service.run_job_manually(job_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Job executed successfully',
                'execution_info': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error running scheduled job: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to run scheduled job'
        }), 500

@backup_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for backup service"""
    return jsonify({
        'success': True,
        'service': 'backup',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200