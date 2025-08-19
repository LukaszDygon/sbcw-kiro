/**
 * NotificationCenter component for real-time notifications
 */
import React, { useState, useEffect, useCallback } from 'react'
import { Notification, NotificationPriority } from '../types'
import notificationService from '../services/notifications'
import { useNotifications } from '../hooks/useNotifications'
import LoadingSpinner from './shared/LoadingSpinner'

interface NotificationCenterProps {
  isOpen: boolean
  onClose: () => void
  onNotificationClick?: (notification: Notification) => void
}

interface NotificationItemProps {
  notification: Notification
  onClick?: (notification: Notification) => void
  onMarkAsRead: (id: string) => void
  onDelete: (id: string) => void
}

const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onClick,
  onMarkAsRead,
  onDelete
}) => {
  const icon = notificationService.getNotificationIcon(notification.type)
  const colorClasses = notificationService.getNotificationColor(notification.priority)
  const timeAgo = notificationService.formatNotificationTime(notification.created_at)
  const isActionable = notificationService.isActionableNotification(notification)

  const handleClick = () => {
    if (!notification.read) {
      onMarkAsRead(notification.id)
    }
    if (onClick) {
      onClick(notification)
    }
  }

  const handleMarkAsRead = (e: React.MouseEvent) => {
    e.stopPropagation()
    onMarkAsRead(notification.id)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDelete(notification.id)
  }

  return (
    <div
      className={`p-4 border-l-4 cursor-pointer transition-colors hover:bg-gray-50 ${
        notification.read ? 'opacity-75' : ''
      } ${colorClasses}`}
      onClick={handleClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          <span className="text-2xl flex-shrink-0">{icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h4 className={`text-sm font-medium ${notification.read ? 'text-gray-600' : 'text-gray-900'}`}>
                {notification.title}
              </h4>
              <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
                {timeAgo}
              </span>
            </div>
            <p className={`text-sm mt-1 ${notification.read ? 'text-gray-500' : 'text-gray-700'}`}>
              {notification.message}
            </p>
            {notification.priority === NotificationPriority.URGENT && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 mt-2">
                Urgent
              </span>
            )}
            {isActionable && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mt-2">
                Action Required
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2 ml-4">
          {!notification.read && (
            <button
              onClick={handleMarkAsRead}
              className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
              title="Mark as read"
            >
              Mark read
            </button>
          )}
          <button
            onClick={handleDelete}
            className="text-xs text-red-600 hover:text-red-800 transition-colors"
            title="Delete notification"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({
  isOpen,
  onClose,
  onNotificationClick
}) => {
  const {
    notifications: allNotifications,
    unreadCount,
    loading,
    error,
    markAsRead,
    markAllAsRead,
    deleteNotification: deleteNotificationFromService
  } = useNotifications()
  
  const [showUnreadOnly, setShowUnreadOnly] = useState(false)
  const [displayedNotifications, setDisplayedNotifications] = useState<Notification[]>([])

  // Filter notifications based on showUnreadOnly
  useEffect(() => {
    if (showUnreadOnly) {
      setDisplayedNotifications(allNotifications.filter(n => !n.read))
    } else {
      setDisplayedNotifications(allNotifications)
    }
  }, [allNotifications, showUnreadOnly])

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await markAsRead(notificationId)
    } catch (err: any) {
      console.error('Failed to mark notification as read:', err)
    }
  }

  const handleMarkAllAsRead = async () => {
    try {
      await markAllAsRead()
    } catch (err: any) {
      console.error('Failed to mark all notifications as read:', err)
    }
  }

  const handleDelete = async (notificationId: string) => {
    try {
      await deleteNotificationFromService(notificationId)
    } catch (err: any) {
      console.error('Failed to delete notification:', err)
    }
  }

  const handleNotificationClick = (notification: Notification) => {
    if (onNotificationClick) {
      onNotificationClick(notification)
    }
    
    // Get action URL and navigate if available
    const actionUrl = notificationService.getNotificationActionUrl(notification)
    if (actionUrl) {
      // In a real app, you'd use React Router here
      console.log('Navigate to:', actionUrl)
    }
  }

  const displayedUnreadCount = displayedNotifications.filter(n => !n.read).length

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />
      <div className="absolute right-0 top-0 h-full w-full max-w-md bg-white shadow-xl">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-white">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Notifications
                {displayedUnreadCount > 0 && (
                  <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    {displayedUnreadCount} unread
                  </span>
                )}
              </h2>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* Controls */}
            <div className="flex items-center justify-between mt-4">
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={showUnreadOnly}
                    onChange={(e) => setShowUnreadOnly(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Unread only</span>
                </label>
              </div>
              
              {displayedUnreadCount > 0 && (
                <button
                  onClick={handleMarkAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Mark all read
                </button>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {error && (
              <div className="p-4 bg-red-50 border-l-4 border-red-400">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {loading && displayedNotifications.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : displayedNotifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 px-6">
                <svg className="w-12 h-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5-5-5h5v-12" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No notifications</h3>
                <p className="text-sm text-gray-500 text-center">
                  {showUnreadOnly ? "You don't have any unread notifications." : "You don't have any notifications yet."}
                </p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {displayedNotifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onClick={handleNotificationClick}
                    onMarkAsRead={handleMarkAsRead}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default NotificationCenter