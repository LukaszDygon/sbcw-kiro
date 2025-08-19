/**
 * NotificationManager component for managing real-time notification toasts
 */
import React, { useState, useEffect } from 'react'
import type { Notification } from '../types'
import { useNotifications } from '../hooks/useNotifications'
import NotificationToast from './NotificationToast'
import notificationService from '../services/notifications'

interface ToastNotification extends Notification {
  toastId: string
}

const NotificationManager: React.FC = () => {
  const { requestPermission } = useNotifications()
  const [toasts, setToasts] = useState<ToastNotification[]>([])
  const [permissionRequested, setPermissionRequested] = useState(false)

  // Request notification permission on first load
  useEffect(() => {
    if (!permissionRequested) {
      requestPermission().then(() => {
        setPermissionRequested(true)
      })
    }
  }, [requestPermission, permissionRequested])

  // Handle new notifications
  useEffect(() => {
    const unsubscribe = notificationService.onNewNotification((notification) => {
      // Add toast notification
      const toastNotification: ToastNotification = {
        ...notification,
        toastId: `toast-${notification.id}-${Date.now()}`
      }
      
      setToasts(prev => [...prev, toastNotification])
      
      // Show browser notification if permission granted
      if ('Notification' in window && Notification.permission === 'granted') {
        const browserNotification = new Notification(notification.title, {
          body: notification.message,
          icon: '/favicon.ico',
          badge: '/favicon.ico',
          tag: notification.id,
          requireInteraction: notification.priority === 'URGENT'
        })

        browserNotification.onclick = () => {
          window.focus()
          const actionUrl = notificationService.getNotificationActionUrl(notification)
          if (actionUrl) {
            // In a real app, you'd use React Router here
            window.location.href = actionUrl
          }
          browserNotification.close()
        }

        // Auto-close after 5 seconds for non-urgent notifications
        if (notification.priority !== 'URGENT') {
          setTimeout(() => browserNotification.close(), 5000)
        }
      }
    })

    return unsubscribe
  }, [])

  const handleCloseToast = (toastId: string) => {
    setToasts(prev => prev.filter(toast => toast.toastId !== toastId))
  }

  const handleToastAction = (notification: Notification) => {
    const actionUrl = notificationService.getNotificationActionUrl(notification)
    if (actionUrl) {
      // In a real app, you'd use React Router here
      window.location.href = actionUrl
    }
  }

  return (
    <div className="fixed top-0 right-0 z-50 p-4 space-y-2 pointer-events-none">
      {toasts.map((toast) => (
        <div key={toast.toastId} className="pointer-events-auto">
          <NotificationToast
            notification={toast}
            onClose={() => handleCloseToast(toast.toastId)}
            onAction={() => handleToastAction(toast)}
          />
        </div>
      ))}
    </div>
  )
}

export default NotificationManager