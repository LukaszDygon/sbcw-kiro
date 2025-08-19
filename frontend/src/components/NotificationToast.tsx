/**
 * NotificationToast component for displaying real-time notification alerts
 */
import React, { useState, useEffect } from 'react'
import { Notification, NotificationPriority } from '../types'
import notificationService from '../services/notifications'

interface NotificationToastProps {
  notification: Notification
  onClose: () => void
  onAction?: () => void
  autoClose?: boolean
  duration?: number
}

const NotificationToast: React.FC<NotificationToastProps> = ({
  notification,
  onClose,
  onAction,
  autoClose = true,
  duration = 5000
}) => {
  const [isVisible, setIsVisible] = useState(false)
  const [isClosing, setIsClosing] = useState(false)

  useEffect(() => {
    // Animate in
    const timer = setTimeout(() => setIsVisible(true), 100)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (autoClose && notification.priority !== NotificationPriority.URGENT) {
      const timer = setTimeout(() => {
        handleClose()
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [autoClose, duration, notification.priority])

  const handleClose = () => {
    setIsClosing(true)
    setTimeout(() => {
      onClose()
    }, 300) // Match animation duration
  }

  const handleAction = () => {
    if (onAction) {
      onAction()
    }
    handleClose()
  }

  const icon = notificationService.getNotificationIcon(notification.type)
  const priorityColors = {
    [NotificationPriority.LOW]: 'bg-gray-50 border-gray-200 text-gray-800',
    [NotificationPriority.MEDIUM]: 'bg-blue-50 border-blue-200 text-blue-800',
    [NotificationPriority.HIGH]: 'bg-orange-50 border-orange-200 text-orange-800',
    [NotificationPriority.URGENT]: 'bg-red-50 border-red-200 text-red-800'
  }

  const isActionable = notificationService.isActionableNotification(notification)

  return (
    <div
      className={`fixed top-4 right-4 z-50 max-w-sm w-full transform transition-all duration-300 ease-in-out ${
        isVisible && !isClosing
          ? 'translate-x-0 opacity-100'
          : 'translate-x-full opacity-0'
      }`}
    >
      <div
        className={`rounded-lg shadow-lg border-l-4 p-4 ${
          priorityColors[notification.priority]
        }`}
      >
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <span className="text-2xl">{icon}</span>
          </div>
          <div className="ml-3 flex-1">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">{notification.title}</h4>
              <button
                onClick={handleClose}
                className="ml-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="text-sm mt-1">{notification.message}</p>
            
            {notification.priority === NotificationPriority.URGENT && (
              <div className="mt-2">
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  Urgent
                </span>
              </div>
            )}
            
            {isActionable && (
              <div className="mt-3 flex space-x-2">
                <button
                  onClick={handleAction}
                  className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors"
                >
                  View Details
                </button>
                <button
                  onClick={handleClose}
                  className="text-xs bg-gray-200 text-gray-700 px-3 py-1 rounded hover:bg-gray-300 transition-colors"
                >
                  Dismiss
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotificationToast