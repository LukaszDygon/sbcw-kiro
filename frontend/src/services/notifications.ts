/**
 * Notification service for SoftBankCashWire frontend
 */
import apiClient, { handleApiError } from './api'
import type { Notification, NotificationType, NotificationPriority } from '../types'

export interface NotificationFilters {
  unread_only?: boolean
  limit?: number
  offset?: number
}

export interface NotificationResponse {
  notifications: Notification[]
  count: number
  has_more: boolean
}

export interface UnreadCountResponse {
  unread_count: number
}

export interface BroadcastNotificationRequest {
  type: NotificationType
  title: string
  message: string
  priority?: NotificationPriority
  data?: Record<string, any>
  expires_in_days?: number
}

export interface TestNotificationRequest {
  type: NotificationType
  title: string
  message: string
  priority?: NotificationPriority
  data?: Record<string, any>
  expires_in_days?: number
}

class NotificationService {
  private eventSource: EventSource | null = null
  private listeners: Set<(notification: Notification) => void> = new Set()
  private unreadCountListeners: Set<(count: number) => void> = new Set()

  /**
   * Initialize real-time notification updates
   */
  initializeRealTimeUpdates(): void {
    if (this.eventSource) {
      return // Already initialized
    }

    try {
      // Create EventSource for server-sent events
      this.eventSource = new EventSource('/api/notifications/stream', {
        withCredentials: true
      })

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'notification') {
            // Notify all listeners about new notification
            this.listeners.forEach(listener => listener(data.notification))
          } else if (data.type === 'unread_count') {
            // Update unread count
            this.unreadCountListeners.forEach(listener => listener(data.count))
          }
        } catch (error) {
          console.error('Error parsing notification event:', error)
        }
      }

      this.eventSource.onerror = (error) => {
        console.error('Notification stream error:', error)
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          this.reconnectRealTimeUpdates()
        }, 5000)
      }

      this.eventSource.onopen = () => {
        console.log('Real-time notifications connected')
      }
    } catch (error) {
      console.error('Failed to initialize real-time notifications:', error)
    }
  }

  /**
   * Reconnect real-time updates
   */
  private reconnectRealTimeUpdates(): void {
    this.closeRealTimeUpdates()
    this.initializeRealTimeUpdates()
  }

  /**
   * Close real-time notification updates
   */
  closeRealTimeUpdates(): void {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
  }

  /**
   * Subscribe to new notifications
   */
  onNewNotification(callback: (notification: Notification) => void): () => void {
    this.listeners.add(callback)
    return () => this.listeners.delete(callback)
  }

  /**
   * Subscribe to unread count updates
   */
  onUnreadCountUpdate(callback: (count: number) => void): () => void {
    this.unreadCountListeners.add(callback)
    return () => this.unreadCountListeners.delete(callback)
  }

  /**
   * Show browser notification (if permission granted)
   */
  private showBrowserNotification(notification: Notification): void {
    if ('Notification' in window && Notification.permission === 'granted') {
      const browserNotification = new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: notification.id,
        requireInteraction: notification.priority === NotificationPriority.URGENT
      })

      browserNotification.onclick = () => {
        window.focus()
        const actionUrl = this.getNotificationActionUrl(notification)
        if (actionUrl) {
          // Navigate to the relevant page
          window.location.href = actionUrl
        }
        browserNotification.close()
      }

      // Auto-close after 5 seconds for non-urgent notifications
      if (notification.priority !== NotificationPriority.URGENT) {
        setTimeout(() => browserNotification.close(), 5000)
      }
    }
  }

  /**
   * Request browser notification permission
   */
  async requestNotificationPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      return 'denied'
    }

    if (Notification.permission === 'default') {
      return await Notification.requestPermission()
    }

    return Notification.permission
  }

  /**
   * Get notifications for the current user
   */
  async getNotifications(filters: NotificationFilters = {}): Promise<NotificationResponse> {
    try {
      const params = new URLSearchParams()
      
      if (filters.unread_only !== undefined) {
        params.append('unread_only', filters.unread_only.toString())
      }
      if (filters.limit !== undefined) {
        params.append('limit', filters.limit.toString())
      }
      if (filters.offset !== undefined) {
        params.append('offset', filters.offset.toString())
      }
      
      const response = await apiClient.get(`/notifications?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get count of unread notifications
   */
  async getUnreadCount(): Promise<number> {
    try {
      const response = await apiClient.get('/notifications/unread-count')
      return response.data.unread_count
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Mark a specific notification as read
   */
  async markAsRead(notificationId: string): Promise<void> {
    try {
      await apiClient.put(`/notifications/${notificationId}/read`)
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<{ count: number }> {
    try {
      const response = await apiClient.put('/notifications/mark-all-read')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Delete a specific notification
   */
  async deleteNotification(notificationId: string): Promise<void> {
    try {
      await apiClient.delete(`/notifications/${notificationId}`)
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Create a test notification (development only)
   */
  async createTestNotification(request: TestNotificationRequest): Promise<Notification> {
    try {
      const response = await apiClient.post('/notifications/test', request)
      return response.data.notification
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Broadcast notification to all users (admin only)
   */
  async broadcastNotification(request: BroadcastNotificationRequest): Promise<{ recipients_count: number }> {
    try {
      const response = await apiClient.post('/notifications/broadcast', request)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Clean up expired notifications (admin only)
   */
  async cleanupExpiredNotifications(): Promise<{ deleted_count: number }> {
    try {
      const response = await apiClient.post('/notifications/cleanup')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get notification icon based on type
   */
  getNotificationIcon(type: NotificationType): string {
    switch (type) {
      case NotificationType.TRANSACTION_RECEIVED:
        return '💰'
      case NotificationType.TRANSACTION_SENT:
        return '📤'
      case NotificationType.MONEY_REQUEST_RECEIVED:
        return '💸'
      case NotificationType.MONEY_REQUEST_APPROVED:
        return '✅'
      case NotificationType.MONEY_REQUEST_DECLINED:
        return '❌'
      case NotificationType.EVENT_CONTRIBUTION:
        return '🎉'
      case NotificationType.EVENT_DEADLINE_APPROACHING:
        return '⏰'
      case NotificationType.EVENT_CLOSED:
        return '🔒'
      case NotificationType.SYSTEM_MAINTENANCE:
        return '🔧'
      case NotificationType.SECURITY_ALERT:
        return '🚨'
      default:
        return '📢'
    }
  }

  /**
   * Get notification color based on priority
   */
  getNotificationColor(priority: NotificationPriority): string {
    switch (priority) {
      case NotificationPriority.LOW:
        return 'text-gray-600 bg-gray-50 border-gray-200'
      case NotificationPriority.MEDIUM:
        return 'text-blue-600 bg-blue-50 border-blue-200'
      case NotificationPriority.HIGH:
        return 'text-orange-600 bg-orange-50 border-orange-200'
      case NotificationPriority.URGENT:
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  /**
   * Format notification time
   */
  formatNotificationTime(createdAt: string): string {
    const now = new Date()
    const notificationTime = new Date(createdAt)
    const diffInMinutes = Math.floor((now.getTime() - notificationTime.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) {
      return 'Just now'
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`
    } else if (diffInMinutes < 1440) { // 24 hours
      const hours = Math.floor(diffInMinutes / 60)
      return `${hours}h ago`
    } else {
      const days = Math.floor(diffInMinutes / 1440)
      if (days === 1) {
        return 'Yesterday'
      } else if (days < 7) {
        return `${days}d ago`
      } else {
        return notificationTime.toLocaleDateString()
      }
    }
  }

  /**
   * Check if notification is actionable (has associated actions)
   */
  isActionableNotification(notification: Notification): boolean {
    return [
      NotificationType.MONEY_REQUEST_RECEIVED,
      NotificationType.EVENT_DEADLINE_APPROACHING
    ].includes(notification.type)
  }

  /**
   * Get action URL for actionable notifications
   */
  getNotificationActionUrl(notification: Notification): string | null {
    switch (notification.type) {
      case NotificationType.MONEY_REQUEST_RECEIVED:
        return `/money-requests/${notification.data?.request_id}`
      case NotificationType.EVENT_DEADLINE_APPROACHING:
        return `/events/${notification.data?.event_id}`
      case NotificationType.TRANSACTION_RECEIVED:
      case NotificationType.TRANSACTION_SENT:
        return `/transactions/${notification.data?.transaction_id}`
      case NotificationType.EVENT_CONTRIBUTION:
      case NotificationType.EVENT_CLOSED:
        return `/events/${notification.data?.event_id}`
      default:
        return null
    }
  }
}

export default new NotificationService()