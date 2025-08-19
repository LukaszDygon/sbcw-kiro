/**
 * AuthGuard component for protecting routes
 */
import React, { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import AuthService from '../../services/auth'
import { UserRole } from '../../types'
import LoadingSpinner from '../shared/LoadingSpinner'

interface AuthGuardProps {
  children: React.ReactNode
  requiredRole?: UserRole
  requiredPermission?: string
}

const AuthGuard: React.FC<AuthGuardProps> = ({ 
  children, 
  requiredRole, 
  requiredPermission 
}) => {
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [hasAccess, setHasAccess] = useState(false)
  const location = useLocation()

  useEffect(() => {
    checkAuthentication()
  }, [requiredRole, requiredPermission])

  const checkAuthentication = async () => {
    try {
      setIsLoading(true)

      // Check if user is authenticated
      if (!AuthService.isAuthenticated()) {
        setIsAuthenticated(false)
        setIsLoading(false)
        return
      }

      // Check if token is expired
      if (AuthService.isTokenExpired()) {
        try {
          await AuthService.refreshToken()
        } catch {
          setIsAuthenticated(false)
          setIsLoading(false)
          return
        }
      }

      // Validate token with backend
      try {
        await AuthService.validateToken()
        setIsAuthenticated(true)
      } catch {
        setIsAuthenticated(false)
        setIsLoading(false)
        return
      }

      // Check role requirement
      if (requiredRole) {
        const user = AuthService.getStoredUser()
        if (!user || !checkRoleAccess(user.role, requiredRole)) {
          setHasAccess(false)
          setIsLoading(false)
          return
        }
      }

      // Check permission requirement
      if (requiredPermission) {
        try {
          const hasPermission = await AuthService.hasPermission(requiredPermission)
          if (!hasPermission) {
            setHasAccess(false)
            setIsLoading(false)
            return
          }
        } catch {
          setHasAccess(false)
          setIsLoading(false)
          return
        }
      }

      setHasAccess(true)
    } catch (error) {
      console.error('Authentication check failed:', error)
      setIsAuthenticated(false)
      setHasAccess(false)
    } finally {
      setIsLoading(false)
    }
  }

  const checkRoleAccess = (userRole: UserRole, requiredRole: UserRole): boolean => {
    // Role hierarchy: FINANCE > ADMIN > EMPLOYEE
    const roleHierarchy = {
      [UserRole.EMPLOYEE]: 1,
      [UserRole.ADMIN]: 2,
      [UserRole.FINANCE]: 3,
    }

    const userLevel = roleHierarchy[userRole] || 0
    const requiredLevel = roleHierarchy[requiredRole] || 0

    return userLevel >= requiredLevel
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  if (!isAuthenticated) {
    // Redirect to login with return URL
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if ((requiredRole || requiredPermission) && !hasAccess) {
    // Redirect to unauthorized page or dashboard
    return <Navigate to="/unauthorized" replace />
  }

  return <>{children}</>
}

export default AuthGuard