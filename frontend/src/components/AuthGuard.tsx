/**
 * AuthGuard component for route protection
 * Handles authentication checks, role-based access, and session management
 */
import React, { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import AuthService, { AuthState, AuthEventType } from '../services/auth'
import LoadingSpinner from './shared/LoadingSpinner'
import { User } from '../types'

// Development mode - bypass authentication
const isDevelopment = import.meta.env.DEV || import.meta.env.VITE_DISABLE_AUTH === 'true'

// Function to fetch the real admin user from database in development mode
const fetchDevelopmentUser = async (): Promise<User> => {
  try {
    // In development mode, we'll fetch the admin user from the database
    const response = await fetch('/api/dev/admin-user', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (response.ok) {
      const userData = await response.json()
      return userData.user
    } else {
      console.warn('Failed to fetch admin user from database, using fallback')
      throw new Error('Failed to fetch admin user')
    }
  } catch (error) {
    console.warn('Development mode: Using fallback admin user', error)
    // Fallback to a basic admin user if API call fails
    return {
      id: 'dev-admin-fallback',
      name: 'Development Admin (Fallback)',
      email: 'admin@dev.local',
      role: 'ADMIN',
      account_status: 'ACTIVE',
      created_at: '2024-01-01T00:00:00Z',
      last_login: new Date().toISOString(),
      permissions: ['*']
    }
  }
}

interface AuthGuardProps {
  children: React.ReactNode
  requiredRole?: string | string[]
  requiredPermissions?: string | string[]
  requireAll?: boolean // If true, user must have ALL permissions/roles
  fallbackPath?: string
  showLoading?: boolean
}

interface AuthGuardState extends AuthState {
  isInitialized: boolean
}

const AuthGuard: React.FC<AuthGuardProps> = ({
  children,
  requiredRole,
  requiredPermissions,
  requireAll = false,
  fallbackPath = '/login',
  showLoading = true
}) => {
  const location = useLocation()
  const [authState, setAuthState] = useState<AuthGuardState>({
    ...AuthService.getAuthState(),
    isInitialized: false
  })

  useEffect(() => {
    let isMounted = true

    const initializeAuth = async () => {
      try {
        if (isDevelopment) {
          // Development mode - fetch real admin user from database
          console.log('🚀 Development mode: Fetching admin user from database')
          try {
            const adminUser = await fetchDevelopmentUser()
            if (isMounted) {
              setAuthState({
                isAuthenticated: true,
                isLoading: false,
                user: adminUser,
                permissions: ['*'],
                error: null,
                sessionInfo: {
                  session_id: 'dev-session-001',
                  expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours
                  ip_address: '127.0.0.1',
                  user_agent: navigator.userAgent,
                  last_activity: new Date().toISOString()
                },
                isInitialized: true
              })
            }
          } catch (error) {
            console.error('Development mode: Failed to fetch admin user', error)
            if (isMounted) {
              setAuthState(prev => ({
                ...prev,
                isInitialized: true,
                isAuthenticated: false,
                error: 'Failed to load development user'
              }))
            }
          }
          return
        }

        const user = await AuthService.initialize()
        
        if (isMounted) {
          setAuthState({
            ...AuthService.getAuthState(),
            isInitialized: true
          })
        }
      } catch (error) {
        console.error('Auth initialization failed:', error)
        if (isMounted) {
          setAuthState(prev => ({
            ...prev,
            isInitialized: true,
            isAuthenticated: false,
            error: 'Authentication failed'
          }))
        }
      }
    }

    // Initialize authentication
    initializeAuth()

    if (!isDevelopment) {
      // Set up event listeners only in production
      const handleAuthEvent = (event: AuthEventType, data?: any) => {
        if (isMounted) {
          setAuthState({
            ...AuthService.getAuthState(),
            isInitialized: true
          })
        }
      }

      AuthService.addEventListener('login', handleAuthEvent)
      AuthService.addEventListener('logout', handleAuthEvent)
      AuthService.addEventListener('session_expired', handleAuthEvent)
      AuthService.addEventListener('permission_changed', handleAuthEvent)

      return () => {
        isMounted = false
        AuthService.removeEventListener('login', handleAuthEvent)
        AuthService.removeEventListener('logout', handleAuthEvent)
        AuthService.removeEventListener('session_expired', handleAuthEvent)
        AuthService.removeEventListener('permission_changed', handleAuthEvent)
      }
    }

    return () => {
      isMounted = false
    }
  }, [])

  // Show loading spinner while initializing
  if (!authState.isInitialized) {
    return showLoading ? (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" message="Initializing authentication..." />
      </div>
    ) : null
  }

  // Show loading spinner during auth operations
  if (authState.isLoading) {
    return showLoading ? (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" message="Authenticating..." />
      </div>
    ) : null
  }

  // Redirect to login if not authenticated (skip in development mode)
  if (!authState.isAuthenticated || !authState.user) {
    if (isDevelopment) {
      // In development, this shouldn't happen since we set fake user above
      console.warn('Development mode: User not set properly')
    } else {
      const redirectUrl = encodeURIComponent(location.pathname + location.search)
      return <Navigate to={`${fallbackPath}?redirect=${redirectUrl}`} replace />
    }
  }

  // Check role requirements (skip in development mode)
  if (requiredRole && !isDevelopment) {
    const roles = Array.isArray(requiredRole) ? requiredRole : [requiredRole]
    const hasRequiredRole = requireAll 
      ? AuthService.hasAnyRole(roles) // For roles, "requireAll" means user needs ANY of the roles
      : AuthService.hasAnyRole(roles)

    if (!hasRequiredRole) {
      return <Navigate to="/unauthorized" replace />
    }
  }

  // Check permission requirements (skip in development mode)
  if (requiredPermissions && !isDevelopment) {
    const permissions = Array.isArray(requiredPermissions) ? requiredPermissions : [requiredPermissions]
    const hasRequiredPermissions = requireAll
      ? AuthService.hasAllPermissions(permissions)
      : AuthService.hasAnyPermission(permissions)

    if (!hasRequiredPermissions) {
      return <Navigate to="/unauthorized" replace />
    }
  }

  // Show error state if there's an auth error
  if (authState.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-red-600 text-lg font-semibold mb-2">
            Authentication Error
          </div>
          <div className="text-gray-600 mb-4">
            {authState.error}
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Render protected content
  return <>{children}</>
}

export default AuthGuard

// Higher-order component version
export const withAuthGuard = (
  Component: React.ComponentType<any>,
  options?: Omit<AuthGuardProps, 'children'>
) => {
  return (props: any) => (
    <AuthGuard {...options}>
      <Component {...props} />
    </AuthGuard>
  )
}

// Hook for accessing auth state in components
export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>(() => {
    if (isDevelopment) {
      return {
        isAuthenticated: false, // Will be set to true after fetching user
        isLoading: true, // Start with loading state
        user: null,
        permissions: [],
        error: null,
        sessionInfo: null
      }
    }
    return AuthService.getAuthState()
  })

  // Fetch development user on mount
  useEffect(() => {
    if (isDevelopment && !authState.isAuthenticated && !authState.error) {
      fetchDevelopmentUser().then(adminUser => {
        setAuthState({
          isAuthenticated: true,
          isLoading: false,
          user: adminUser,
          permissions: ['*'],
          error: null,
          sessionInfo: {
            session_id: 'dev-session-001',
            expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
            ip_address: '127.0.0.1',
            user_agent: navigator.userAgent,
            last_activity: new Date().toISOString()
          }
        })
      }).catch(error => {
        console.error('useAuth: Failed to fetch development user', error)
        setAuthState(prev => ({
          ...prev,
          isLoading: false,
          error: 'Failed to load development user'
        }))
      })
    }
  }, [authState.isAuthenticated, authState.error])

  useEffect(() => {
    if (isDevelopment) {
      // In development mode, don't set up real auth listeners
      return
    }

    const handleAuthEvent = () => {
      setAuthState(AuthService.getAuthState())
    }

    AuthService.addEventListener('login', handleAuthEvent)
    AuthService.addEventListener('logout', handleAuthEvent)
    AuthService.addEventListener('session_expired', handleAuthEvent)
    AuthService.addEventListener('permission_changed', handleAuthEvent)
    AuthService.addEventListener('token_refresh', handleAuthEvent)

    return () => {
      AuthService.removeEventListener('login', handleAuthEvent)
      AuthService.removeEventListener('logout', handleAuthEvent)
      AuthService.removeEventListener('session_expired', handleAuthEvent)
      AuthService.removeEventListener('permission_changed', handleAuthEvent)
      AuthService.removeEventListener('token_refresh', handleAuthEvent)
    }
  }, [])

  const developmentMethods = {
    login: async () => console.log('Development mode: Login bypassed'),
    logout: () => console.log('Development mode: Logout bypassed'),
    hasRole: (role: string) => true, // Admin has all roles
    hasAnyRole: (roles: string[]) => true,
    hasPermission: (permission: string) => true, // Admin has all permissions
    hasAnyPermission: (permissions: string[]) => true,
    hasAllPermissions: (permissions: string[]) => true,
    isAdmin: () => true,
    isFinance: () => true,
    refreshToken: async () => console.log('Development mode: Token refresh bypassed'),
    updatePermissions: async () => ['*']
  }

  const productionMethods = {
    login: AuthService.loginWithMicrosoft,
    logout: AuthService.logout,
    hasRole: AuthService.hasRole,
    hasAnyRole: AuthService.hasAnyRole,
    hasPermission: AuthService.hasPermission,
    hasAnyPermission: AuthService.hasAnyPermission,
    hasAllPermissions: AuthService.hasAllPermissions,
    isAdmin: AuthService.isAdmin,
    isFinance: AuthService.isFinance,
    refreshToken: AuthService.forceRefreshToken,
    updatePermissions: AuthService.updatePermissions
  }

  return {
    ...authState,
    ...(isDevelopment ? developmentMethods : productionMethods)
  }
}

// Hook for session management
export const useSession = () => {
  const [sessionInfo, setSessionInfo] = useState(() => {
    if (isDevelopment) {
      return {
        session_id: 'dev-session-001',
        expires_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // 24 hours
        ip_address: '127.0.0.1',
        user_agent: navigator.userAgent,
        last_activity: new Date().toISOString()
      }
    }
    return AuthService.getSessionInfo()
  })

  useEffect(() => {
    if (isDevelopment) {
      // In development mode, don't set up real session listeners
      return
    }

    const handleSessionEvent = () => {
      setSessionInfo(AuthService.getSessionInfo())
    }

    AuthService.addEventListener('login', handleSessionEvent)
    AuthService.addEventListener('session_expired', handleSessionEvent)
    AuthService.addEventListener('token_refresh', handleSessionEvent)

    return () => {
      AuthService.removeEventListener('login', handleSessionEvent)
      AuthService.removeEventListener('session_expired', handleSessionEvent)
      AuthService.removeEventListener('token_refresh', handleSessionEvent)
    }
  }, [])

  const getTimeUntilExpiry = () => {
    if (!sessionInfo?.expires_at) return 0
    if (isDevelopment) return 24 * 60 * 60 * 1000 // 24 hours in development
    return Math.max(0, new Date(sessionInfo.expires_at).getTime() - Date.now())
  }

  const extendSession = async () => {
    if (isDevelopment) {
      console.log('Development mode: Session extension bypassed')
      return
    }
    
    try {
      await AuthService.forceRefreshToken()
      setSessionInfo(AuthService.getSessionInfo())
    } catch (error) {
      console.error('Failed to extend session:', error)
      throw error
    }
  }

  return {
    sessionInfo,
    getTimeUntilExpiry,
    extendSession
  }
}