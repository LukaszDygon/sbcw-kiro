/**
 * NotificationBell component for displaying notification count and opening notification center
 */
import React, { useState, useEffect } from 'react'
import { useNotifications } from '../hooks/useNotifications'

interface NotificationBellProps {
  onClick: () => void
  className?: string
}

const NotificationBell: React.FC<NotificationBellProps> = ({ onClick, className = '' }) => {
  const { unreadCount, loading } = useNotifications()
  const [isAnimating, setIsAnimating] = useState(false)

  // Animate bell when unread count changes
  useEffect(() => {
    if (unreadCount > 0) {
      setIsAnimating(true)
      const timer = setTimeout(() => setIsAnimating(false), 1000)
      return () => clearTimeout(timer)
    }
  }, [unreadCount])

  return (
    <button
      onClick={onClick}
      className={`relative p-2 text-gray-600 hover:text-gray-900 transition-colors ${className} ${
        isAnimating ? 'animate-bounce' : ''
      }`}
      title={`${unreadCount} unread notifications`}
      disabled={loading}
    >
      <svg
        className="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 17h5l-5 5-5-5h5v-12"
        />
      </svg>
      
      {/* Notification badge */}
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full min-w-[1.25rem] h-5">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
      
      {/* Loading indicator */}
      {loading && (
        <span className="absolute -top-1 -right-1 inline-flex items-center justify-center w-3 h-3 bg-blue-600 rounded-full animate-pulse" />
      )}
    </button>
  )
}

export default NotificationBell