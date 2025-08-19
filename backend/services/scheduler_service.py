"""
Scheduler service for SoftBankCashWire
Handles automated backup and data retention tasks
"""
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from services.backup_service import BackupService
from services.data_retention_service import DataRetentionService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for managing automated tasks"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self.job_history = []
        self.max_history = 100
    
    def _log_job_execution(self, job_name: str, success: bool, result: Dict[str, Any] = None, error: str = None):
        """Log job execution results"""
        log_entry = {
            'job_name': job_name,
            'executed_at': datetime.utcnow().isoformat(),
            'success': success,
            'result': result,
            'error': error
        }
        
        self.job_history.append(log_entry)
        
        # Keep only recent history
        if len(self.job_history) > self.max_history:
            self.job_history = self.job_history[-self.max_history:]
        
        if success:
            logger.info(f"Scheduled job '{job_name}' completed successfully")
        else:
            logger.error(f"Scheduled job '{job_name}' failed: {error}")
    
    def _daily_backup_job(self):
        """Daily database backup job"""
        try:
            result = BackupService.create_database_backup("daily_auto")
            self._log_job_execution("daily_backup", result['success'], result)
            
            if result['success']:
                # Also cleanup old backups
                cleanup_result = BackupService.cleanup_old_backups()
                logger.info(f"Backup cleanup: {cleanup_result}")
                
        except Exception as e:
            self._log_job_execution("daily_backup", False, error=str(e))
    
    def _weekly_data_cleanup_job(self):
        """Weekly data retention cleanup job"""
        try:
            result = DataRetentionService.run_full_cleanup()
            self._log_job_execution("weekly_cleanup", result['success'], result)
            
        except Exception as e:
            self._log_job_execution("weekly_cleanup", False, error=str(e))
    
    def _hourly_backup_cleanup_job(self):
        """Hourly backup cleanup job"""
        try:
            result = BackupService.cleanup_old_backups()
            self._log_job_execution("backup_cleanup", result['success'], result)
            
        except Exception as e:
            self._log_job_execution("backup_cleanup", False, error=str(e))
    
    def _compliance_check_job(self):
        """Daily compliance validation job"""
        try:
            result = DataRetentionService.validate_retention_compliance()
            self._log_job_execution("compliance_check", result['success'], result)
            
            # Log any compliance violations
            if result['success'] and not result['compliance']['compliant']:
                logger.warning(f"Data retention compliance violations detected: {result['compliance']['violations']}")
                
        except Exception as e:
            self._log_job_execution("compliance_check", False, error=str(e))
    
    def start_scheduler(self) -> Dict[str, Any]:
        """
        Start the automated scheduler
        
        Returns:
            Dictionary with start result
        """
        try:
            if self.is_running:
                return {
                    'success': False,
                    'error': 'Scheduler is already running'
                }
            
            # Add scheduled jobs
            
            # Daily backup at 2 AM
            self.scheduler.add_job(
                func=self._daily_backup_job,
                trigger=CronTrigger(hour=2, minute=0),
                id='daily_backup',
                name='Daily Database Backup',
                replace_existing=True
            )
            
            # Weekly cleanup on Sunday at 3 AM
            self.scheduler.add_job(
                func=self._weekly_data_cleanup_job,
                trigger=CronTrigger(day_of_week=6, hour=3, minute=0),
                id='weekly_cleanup',
                name='Weekly Data Cleanup',
                replace_existing=True
            )
            
            # Hourly backup cleanup
            self.scheduler.add_job(
                func=self._hourly_backup_cleanup_job,
                trigger=IntervalTrigger(hours=1),
                id='backup_cleanup',
                name='Backup Cleanup',
                replace_existing=True
            )
            
            # Daily compliance check at 6 AM
            self.scheduler.add_job(
                func=self._compliance_check_job,
                trigger=CronTrigger(hour=6, minute=0),
                id='compliance_check',
                name='Data Retention Compliance Check',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Automated scheduler started successfully")
            
            return {
                'success': True,
                'message': 'Scheduler started successfully',
                'jobs_scheduled': len(self.scheduler.get_jobs()),
                'started_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_scheduler(self) -> Dict[str, Any]:
        """
        Stop the automated scheduler
        
        Returns:
            Dictionary with stop result
        """
        try:
            if not self.is_running:
                return {
                    'success': False,
                    'error': 'Scheduler is not running'
                }
            
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            
            logger.info("Automated scheduler stopped")
            
            return {
                'success': True,
                'message': 'Scheduler stopped successfully',
                'stopped_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status
        
        Returns:
            Dictionary with scheduler status
        """
        try:
            jobs = []
            
            if self.is_running:
                for job in self.scheduler.get_jobs():
                    jobs.append({
                        'id': job.id,
                        'name': job.name,
                        'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                        'trigger': str(job.trigger)
                    })
            
            return {
                'success': True,
                'is_running': self.is_running,
                'jobs': jobs,
                'job_count': len(jobs),
                'recent_executions': self.job_history[-10:] if self.job_history else [],
                'checked_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get scheduler status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_job_manually(self, job_id: str) -> Dict[str, Any]:
        """
        Manually trigger a scheduled job
        
        Args:
            job_id: ID of the job to run
            
        Returns:
            Dictionary with execution result
        """
        try:
            if not self.is_running:
                return {
                    'success': False,
                    'error': 'Scheduler is not running'
                }
            
            job = self.scheduler.get_job(job_id)
            if not job:
                return {
                    'success': False,
                    'error': f'Job {job_id} not found'
                }
            
            # Run the job immediately
            job.func()
            
            return {
                'success': True,
                'message': f'Job {job_id} executed manually',
                'executed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to run job manually: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_job_history(self, job_name: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get job execution history
        
        Args:
            job_name: Optional job name to filter by
            limit: Maximum number of entries to return
            
        Returns:
            List of job execution history entries
        """
        try:
            history = self.job_history.copy()
            
            if job_name:
                history = [entry for entry in history if entry['job_name'] == job_name]
            
            # Sort by execution time (newest first)
            history.sort(key=lambda x: x['executed_at'], reverse=True)
            
            return history[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get job history: {str(e)}")
            return []
    
    def add_custom_job(self, job_id: str, job_name: str, job_func, trigger_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a custom scheduled job
        
        Args:
            job_id: Unique job identifier
            job_name: Human-readable job name
            job_func: Function to execute
            trigger_config: Trigger configuration (cron or interval)
            
        Returns:
            Dictionary with add result
        """
        try:
            if not self.is_running:
                return {
                    'success': False,
                    'error': 'Scheduler is not running'
                }
            
            # Create trigger based on config
            if trigger_config.get('type') == 'cron':
                trigger = CronTrigger(**trigger_config.get('params', {}))
            elif trigger_config.get('type') == 'interval':
                trigger = IntervalTrigger(**trigger_config.get('params', {}))
            else:
                return {
                    'success': False,
                    'error': 'Invalid trigger type. Use "cron" or "interval"'
                }
            
            self.scheduler.add_job(
                func=job_func,
                trigger=trigger,
                id=job_id,
                name=job_name,
                replace_existing=True
            )
            
            logger.info(f"Added custom job: {job_name} ({job_id})")
            
            return {
                'success': True,
                'message': f'Custom job {job_name} added successfully',
                'job_id': job_id,
                'added_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to add custom job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_job(self, job_id: str) -> Dict[str, Any]:
        """
        Remove a scheduled job
        
        Args:
            job_id: ID of the job to remove
            
        Returns:
            Dictionary with removal result
        """
        try:
            if not self.is_running:
                return {
                    'success': False,
                    'error': 'Scheduler is not running'
                }
            
            job = self.scheduler.get_job(job_id)
            if not job:
                return {
                    'success': False,
                    'error': f'Job {job_id} not found'
                }
            
            self.scheduler.remove_job(job_id)
            
            logger.info(f"Removed job: {job_id}")
            
            return {
                'success': True,
                'message': f'Job {job_id} removed successfully',
                'removed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to remove job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Global scheduler instance
scheduler_service = SchedulerService()