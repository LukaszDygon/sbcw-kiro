/**
 * React hook for managing real-time notifications
 */
import { useState, useEffect, useCallback } from 'react'
import { Notification } from '../types'
import notificationService from '../services/notifications'

interface UseNotificationsReturn {
  notifications: Notification[]
  unreadCount: number
  loading: boolean
  error: string | null
  markAsRead: (notificationId: string) => Promise<void>
  markAllAsRead: () => Promise<void>
  deleteNotification: (notificationId: string) => Promise<void>
  refreshNotifications: () => Promise<void>
  requestPermission: () => Promise<NotificationPermission>
}

export const useNotifications = (): UseNotificationsReturn => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load initial notifications
  const loadNotifications = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [notificationsResponse, unreadCountResponse] = await Promise.all([
        notificationService.getNotifications({ limit: 50 }),
        notificationService.getUnreadCount()
      ])
      
      setNotifications(notificationsResponse.notifications)
      setUnreadCount(unreadCountResponse)
    } catch (err: any) {
      setError(err.message || 'Failed to load notifications')
    } finally {
      setLoading(false)
    }
  }, [])

  // Handle new notification from real-time updates
  const handleNewNotification = useCallback((notification: Notification) => {
    setNotifications(prev => [notification, ...prev])
    if (!notification.read) {
      setUnreadCount(prev => prev + 1)
    }
  }, [])

  // Handle unread count updates
  const handleUnreadCountUpdate = useCallback((count: number) => {
    setUnreadCount(count)
  }, [])

  // Mark notification as read
  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await notificationService.markAsRead(notificationId)
      
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      )
      
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (err: any) {
      setError(err.message || 'Failed to mark notification as read')
    }
  }, [])

  // Mark all notifications as read
  const markAllAsRead = useCallback(async () => {
    try {
      const result = await notificationService.markAllAsRead()
      
      setNotifications(prev => prev.map(n => ({ ...n, read: true })))
      setUnreadCount(0)
    } catch (err: any) {
      setError(err.message || 'Failed to mark all notifications as read')
    }
  }, [])

  // Delete notification
  const deleteNotification = useCallback(async (notificationId: string) => {
    try {
      await notificationService.deleteNotification(notificationId)
      
      const notification = notifications.find(n => n.id === notificationId)
      if (notification && !notification.read) {
        setUnreadCount(prev => Math.max(0, prev - 1))
      }
      
      setNotifications(prev => prev.filter(n => n.id !== notificationId))
    } catch (err: any) {
      setError(err.message || 'Failed to delete notification')
    }
  }, [notifications])

  // Request browser notification permission
  const requestPermission = useCallback(async () => {
    return await notificationService.requestNotificationPermission()
  }, [])

  // Initialize real-time updates and load initial data
  useEffect(() => {
    loadNotifications()
    
    // Initialize real-time updates
    notificationService.initializeRealTimeUpdates()
    
    // Subscribe to real-time updates
    const unsubscribeNotifications = notificationService.onNewNotification(handleNewNotification)
    const unsubscribeUnreadCount = notificationService.onUnreadCountUpdate(handleUnreadCountUpdate)
    
    // Cleanup on unmount
    return () => {
      unsubscribeNotifications()
      unsubscribeUnreadCount()
      notificationService.closeRealTimeUpdates()
    }
  }, [loadNotifications, handleNewNotification, handleUnreadCountUpdate])

  return {
    notifications,
    unreadCount,
    loading,
    error,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    refreshNotifications: loadNotifications,
    requestPermission
  }
}