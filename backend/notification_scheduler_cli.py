#!/usr/bin/env python3
"""
CLI script for running notification scheduler tasks
Can be run as a cron job for automated notifications
"""
import sys
import os
import argparse
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from services.notification_scheduler import NotificationScheduler


def check_deadlines():
    """Check for event deadlines and send notifications"""
    try:
        app = create_app()
        with app.app_context():
            notifications_sent = NotificationScheduler.check_event_deadlines()
            print(f"Deadline check completed. Sent {notifications_sent} notifications.")
            return notifications_sent
    except Exception as e:
        print(f"Error checking deadlines: {str(e)}")
        return 0


def send_maintenance_notification(title: str, message: str, scheduled_time: str = None):
    """Send system maintenance notification"""
    try:
        app = create_app()
        with app.app_context():
            notifications_sent = NotificationScheduler.send_system_maintenance_notification(
                title=title,
                message=message,
                scheduled_time=scheduled_time
            )
            print(f"Maintenance notification sent to {notifications_sent} users.")
            return notifications_sent
    except Exception as e:
        print(f"Error sending maintenance notification: {str(e)}")
        return 0


def send_security_alert(title: str, message: str):
    """Send security alert to all users"""
    try:
        app = create_app()
        with app.app_context():
            notifications_sent = NotificationScheduler.send_security_alert(
                title=title,
                message=message
            )
            print(f"Security alert sent to {notifications_sent} users.")
            return notifications_sent
    except Exception as e:
        print(f"Error sending security alert: {str(e)}")
        return 0


def cleanup_notifications(days_old: int = 30):
    """Clean up old notifications"""
    try:
        app = create_app()
        with app.app_context():
            deleted_count = NotificationScheduler.cleanup_old_notifications(days_old)
            print(f"Cleaned up {deleted_count} old notifications.")
            return deleted_count
    except Exception as e:
        print(f"Error cleaning up notifications: {str(e)}")
        return 0


def main():
    parser = argparse.ArgumentParser(description='SoftBankCashWire Notification Scheduler')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deadline check command
    deadline_parser = subparsers.add_parser('check-deadlines', help='Check event deadlines')
    
    # Maintenance notification command
    maintenance_parser = subparsers.add_parser('maintenance', help='Send maintenance notification')
    maintenance_parser.add_argument('--title', required=True, help='Notification title')
    maintenance_parser.add_argument('--message', required=True, help='Notification message')
    maintenance_parser.add_argument('--scheduled-time', help='Scheduled maintenance time')
    
    # Security alert command
    security_parser = subparsers.add_parser('security-alert', help='Send security alert')
    security_parser.add_argument('--title', required=True, help='Alert title')
    security_parser.add_argument('--message', required=True, help='Alert message')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old notifications')
    cleanup_parser.add_argument('--days-old', type=int, default=30, 
                               help='Delete notifications older than this many days (default: 30)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    print(f"Starting notification scheduler task: {args.command}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        if args.command == 'check-deadlines':
            result = check_deadlines()
        elif args.command == 'maintenance':
            result = send_maintenance_notification(
                title=args.title,
                message=args.message,
                scheduled_time=args.scheduled_time
            )
        elif args.command == 'security-alert':
            result = send_security_alert(
                title=args.title,
                message=args.message
            )
        elif args.command == 'cleanup':
            result = cleanup_notifications(args.days_old)
        else:
            print(f"Unknown command: {args.command}")
            return 1
        
        print(f"Task completed successfully. Result: {result}")
        return 0
        
    except Exception as e:
        print(f"Task failed with error: {str(e)}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)