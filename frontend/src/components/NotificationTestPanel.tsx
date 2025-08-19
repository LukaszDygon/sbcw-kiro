/**
 * NotificationTestPanel component for testing notification functionality
 * Only available in development mode
 */
import React, { useState } from 'react'
import { NotificationType, NotificationPriority } from '../types'
import notificationService from '../services/notifications'

const NotificationTestPanel: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const createTestNotification = async (type: NotificationType, priority: NotificationPriority) => {
    try {
      setLoading(true)
      setMessage('')

      const testNotifications = {
        [NotificationType.TRANSACTION_RECEIVED]: {
          title: 'Money Received',
          message: 'You received £25.00 from John Smith',
          data: { amount: '25.00', sender_name: 'John Smith', transaction_id: 'test-123' }
        },
        [NotificationType.MONEY_REQUEST_RECEIVED]: {
          title: 'Money Request Received',
          message: 'Sarah Johnson is requesting £15.00 from you',
          data: { amount: '15.00', requester_name: 'Sarah Johnson', request_id: 'req-123' }
        },
        [NotificationType.EVENT_DEADLINE_APPROACHING]: {
          title: 'Event Deadline Approaching',
          message: 'The deadline for Team Lunch Fund is approaching (2024-12-15)',
          data: { event_name: 'Team Lunch Fund', deadline: '2024-12-15', event_id: 'event-123' }
        },
        [NotificationType.SYSTEM_MAINTENANCE]: {
          title: 'Scheduled Maintenance',
          message: 'System maintenance scheduled for tonight at 2:00 AM',
          data: { scheduled_time: '2024-12-09 02:00:00' }
        },
        [NotificationType.SECURITY_ALERT]: {
          title: 'Security Alert',
          message: 'Unusual login activity detected from new device',
          data: { severity: 'HIGH', timestamp: new Date().toISOString() }
        }
      }

      const testData = testNotifications[type] || {
        title: 'Test Notification',
        message: 'This is a test notification',
        data: {}
      }

      await notificationService.createTestNotification({
        type,
        title: testData.title,
        message: testData.message,
        priority,
        data: testData.data
      })

      setMessage(`Test notification created: ${testData.title}`)
    } catch (error: any) {
      setMessage(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const requestPermission = async () => {
    try {
      const permission = await notificationService.requestNotificationPermission()
      setMessage(`Browser notification permission: ${permission}`)
    } catch (error: any) {
      setMessage(`Error requesting permission: ${error.message}`)
    }
  }

  // Only show in development mode
  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  return (
    <div className="fixed bottom-4 left-4 bg-white shadow-lg rounded-lg p-4 border max-w-sm">
      <h3 className="text-lg font-semibold mb-4">Notification Test Panel</h3>
      
      <div className="space-y-2 mb-4">
        <button
          onClick={() => createTestNotification(NotificationType.TRANSACTION_RECEIVED, NotificationPriority.MEDIUM)}
          disabled={loading}
          className="w-full text-left px-3 py-2 text-sm bg-green-100 hover:bg-green-200 rounded disabled:opacity-50"
        >
          💰 Transaction Received
        </button>
        
        <button
          onClick={() => createTestNotification(NotificationType.MONEY_REQUEST_RECEIVED, NotificationPriority.HIGH)}
          disabled={loading}
          className="w-full text-left px-3 py-2 text-sm bg-blue-100 hover:bg-blue-200 rounded disabled:opacity-50"
        >
          💸 Money Request
        </button>
        
        <button
          onClick={() => createTestNotification(NotificationType.EVENT_DEADLINE_APPROACHING, NotificationPriority.HIGH)}
          disabled={loading}
          className="w-full text-left px-3 py-2 text-sm bg-orange-100 hover:bg-orange-200 rounded disabled:opacity-50"
        >
          ⏰ Event Deadline
        </button>
        
        <button
          onClick={() => createTestNotification(NotificationType.SYSTEM_MAINTENANCE, NotificationPriority.HIGH)}
          disabled={loading}
          className="w-full text-left px-3 py-2 text-sm bg-yellow-100 hover:bg-yellow-200 rounded disabled:opacity-50"
        >
          🔧 Maintenance
        </button>
        
        <button
          onClick={() => createTestNotification(NotificationType.SECURITY_ALERT, NotificationPriority.URGENT)}
          disabled={loading}
          className="w-full text-left px-3 py-2 text-sm bg-red-100 hover:bg-red-200 rounded disabled:opacity-50"
        >
          🚨 Security Alert
        </button>
      </div>

      <button
        onClick={requestPermission}
        className="w-full px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded mb-2"
      >
        Request Browser Permission
      </button>

      {message && (
        <div className="text-xs text-gray-600 mt-2 p-2 bg-gray-50 rounded">
          {message}
        </div>
      )}
    </div>
  )
}

export default NotificationTestPanel