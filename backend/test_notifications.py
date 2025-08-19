#!/usr/bin/env python3
"""
Simple test script for notification functionality
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import NotificationType, NotificationPriority
from services.notification_service import NotificationService


def test_notification_creation():
    """Test creating a notification"""
    try:
        app = create_app()
        with app.app_context():
            # Create a test notification
            notification = NotificationService.create_notification(
                user_id='test-user-123',
                notification_type=NotificationType.TRANSACTION_RECEIVED,
                title='Test Notification',
                message='This is a test notification',
                priority=NotificationPriority.MEDIUM,
                data={'test': 'data'}
            )
            
            print(f"✅ Notification created successfully: {notification.id}")
            print(f"   Title: {notification.title}")
            print(f"   Message: {notification.message}")
            print(f"   Type: {notification.type.value}")
            print(f"   Priority: {notification.priority.value}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating notification: {str(e)}")
        return False


def test_notification_retrieval():
    """Test retrieving notifications"""
    try:
        app = create_app()
        with app.app_context():
            # Get notifications for test user
            notifications = NotificationService.get_user_notifications(
                user_id='test-user-123',
                limit=10
            )
            
            print(f"✅ Retrieved {len(notifications)} notifications")
            for notification in notifications:
                print(f"   - {notification.title} ({notification.type.value})")
            
            return True
            
    except Exception as e:
        print(f"❌ Error retrieving notifications: {str(e)}")
        return False


def test_unread_count():
    """Test getting unread count"""
    try:
        app = create_app()
        with app.app_context():
            count = NotificationService.get_unread_count('test-user-123')
            print(f"✅ Unread count: {count}")
            return True
            
    except Exception as e:
        print(f"❌ Error getting unread count: {str(e)}")
        return False


def main():
    print("Testing SoftBankCashWire Notification System")
    print("=" * 50)
    
    tests = [
        ("Creating notification", test_notification_creation),
        ("Retrieving notifications", test_notification_retrieval),
        ("Getting unread count", test_unread_count)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed!")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)