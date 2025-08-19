/**
 * Session management component
 * Handles session timeout warnings, automatic logout, and session renewal
 */
import React, { useState, useEffect, useCallback } from 'react'
import AuthService, { AuthEventType } from '../services/auth'

interface SessionManagerProps {
  children: React.ReactNode
  warningMinutes?: number // Show warning X minutes before expiry
  autoLogoutMinutes?: number // Auto logout after X minutes of inactivity
  showWarningDialog?: boolean
}

interface SessionWarningDialogProps {
  isOpen: boolean
  timeRemaining: number
  onExtend: () => void
  onLogout: () => void
}

const SessionWarningDialog: React.FC<SessionWarningDialogProps> = ({
  isOpen,
  timeRemaining,
  onExtend,
  onLogout
}) => {
  if (!isOpen) return null

  const minutes = Math.floor(timeRemaining / 60)
  const seconds = timeRemaining % 60

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
          &#8203;
        </span>

        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div className="sm:flex sm:items-start">
            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 sm:mx-0 sm:h-10 sm:w-10">
              <svg
                className="h-6 w-6 text-yellow-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Session Expiring Soon
              </h3>
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  Your session will expire in{' '}
                  <span className="font-semibold text-red-600">
                    {minutes}:{seconds.toString().padStart(2, '0')}
                  </span>
                  . Would you like to extend your session?
                </p>
              </div>
            </div>
          </div>
          <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={onExtend}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Extend Session
            </button>
            <button
              type="button"
              onClick={onLogout}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
            >
              Logout Now
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

const SessionManager: React.FC<SessionManagerProps> = ({
  children,
  warningMinutes = 5,
  autoLogoutMinutes = 30,
  showWarningDialog = true
}) => {
  const [showWarning, setShowWarning] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [lastActivity, setLastActivity] = useState(Date.now())

  // Track user activity
  const updateActivity = useCallback(() => {
    setLastActivity(Date.now())
  }, [])

  // Handle session extension
  const handleExtendSession = useCallback(async () => {
    try {
      await AuthService.forceRefreshToken()
      setShowWarning(false)
      setLastActivity(Date.now())
    } catch (error) {
      console.error('Failed to extend session:', error)
      // If refresh fails, logout
      AuthService.logout()
    }
  }, [])

  // Handle logout
  const handleLogout = useCallback(() => {
    AuthService.logout()
  }, [])

  // Set up activity listeners
  useEffect(() => {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
    
    events.forEach(event => {
      document.addEventListener(event, updateActivity, true)
    })

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, updateActivity, true)
      })
    }
  }, [updateActivity])

  // Set up session monitoring
  useEffect(() => {
    if (!AuthService.isAuthenticated()) {
      return
    }

    const checkSession = () => {
      const now = Date.now()
      const timeSinceActivity = now - lastActivity
      const inactiveMinutes = timeSinceActivity / (1000 * 60)

      // Check for auto logout due to inactivity
      if (inactiveMinutes >= autoLogoutMinutes) {
        console.log('Auto logout due to inactivity')
        AuthService.logout()
        return
      }

      // Check token expiration
      const tokenExpiration = localStorage.getItem('token_expiration')
      if (tokenExpiration) {
        const expirationTime = parseInt(tokenExpiration)
        const timeUntilExpiry = expirationTime - now
        const minutesUntilExpiry = timeUntilExpiry / (1000 * 60)

        // Show warning if close to expiry
        if (minutesUntilExpiry <= warningMinutes && minutesUntilExpiry > 0) {
          if (showWarningDialog && !showWarning) {
            setShowWarning(true)
          }
          setTimeRemaining(Math.floor(timeUntilExpiry / 1000))
        } else if (minutesUntilExpiry <= 0) {
          // Token expired
          console.log('Token expired, logging out')
          AuthService.logout()
          return
        } else {
          setShowWarning(false)
        }
      }
    }

    // Check immediately
    checkSession()

    // Set up interval to check every 30 seconds
    const interval = setInterval(checkSession, 30000)

    return () => clearInterval(interval)
  }, [lastActivity, warningMinutes, autoLogoutMinutes, showWarningDialog, showWarning])

  // Update countdown timer
  useEffect(() => {
    if (!showWarning) return

    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          // Time's up, logout
          AuthService.logout()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [showWarning])

  // Listen for auth events
  useEffect(() => {
    const handleAuthEvent = (event: AuthEventType) => {
      if (event === 'logout' || event === 'session_expired') {
        setShowWarning(false)
      } else if (event === 'login' || event === 'token_refresh') {
        setShowWarning(false)
        setLastActivity(Date.now())
      }
    }

    AuthService.addEventListener('login', handleAuthEvent)
    AuthService.addEventListener('logout', handleAuthEvent)
    AuthService.addEventListener('session_expired', handleAuthEvent)
    AuthService.addEventListener('token_refresh', handleAuthEvent)

    return () => {
      AuthService.removeEventListener('login', handleAuthEvent)
      AuthService.removeEventListener('logout', handleAuthEvent)
      AuthService.removeEventListener('session_expired', handleAuthEvent)
      AuthService.removeEventListener('token_refresh', handleAuthEvent)
    }
  }, [])

  return (
    <>
      {children}
      <SessionWarningDialog
        isOpen={showWarning}
        timeRemaining={timeRemaining}
        onExtend={handleExtendSession}
        onLogout={handleLogout}
      />
    </>
  )
}

export default SessionManager

// Hook for session information
export const useSession = () => {
  const [sessionInfo, setSessionInfo] = useState(AuthService.getSessionInfo())
  const [isActive, setIsActive] = useState(true)
  const [lastActivity, setLastActivity] = useState(Date.now())

  useEffect(() => {
    const handleAuthEvent = () => {
      setSessionInfo(AuthService.getSessionInfo())
    }

    AuthService.addEventListener('login', handleAuthEvent)
    AuthService.addEventListener('logout', handleAuthEvent)
    AuthService.addEventListener('session_expired', handleAuthEvent)
    AuthService.addEventListener('token_refresh', handleAuthEvent)

    return () => {
      AuthService.removeEventListener('login', handleAuthEvent)
      AuthService.removeEventListener('logout', handleAuthEvent)
      AuthService.removeEventListener('session_expired', handleAuthEvent)
      AuthService.removeEventListener('token_refresh', handleAuthEvent)
    }
  }, [])

  const extendSession = useCallback(async () => {
    try {
      await AuthService.forceRefreshToken()
      setLastActivity(Date.now())
    } catch (error) {
      console.error('Failed to extend session:', error)
      throw error
    }
  }, [])

  const getTimeUntilExpiry = useCallback(() => {
    const tokenExpiration = localStorage.getItem('token_expiration')
    if (!tokenExpiration) return 0

    const expirationTime = parseInt(tokenExpiration)
    const now = Date.now()
    return Math.max(0, expirationTime - now)
  }, [])

  return {
    sessionInfo,
    isActive,
    lastActivity,
    extendSession,
    getTimeUntilExpiry,
    logout: AuthService.logout
  }
}