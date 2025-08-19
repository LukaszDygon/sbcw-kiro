/**
 * Mock AuthGuard component for testing
 * Prevents infinite loops and navigation conflicts in test environment
 */
import React from 'react'

// Mock user data for testing
const mockUser = {
  id: 'test-user-id',
  name: 'Test User',
  email: 'test@example.com',
  role: 'EMPLOYEE',
  permissions: ['read', 'write'],
  microsoft_id: 'test-microsoft-id'
}

// Simplified auth state interface for testing
interface MockAuthState {
  isAuthenticated: boolean
  isInitialized: boolean
  isLoading: boolean
  user: any | null
  error: string | null
}

// Default authenticated state
const defaultAuthState: MockAuthState = {
  isAuthenticated: true,
  isInitialized: true,
  isLoading: false,
  user: mockUser,
  error: null
}

// Global mock state that can be controlled by tests
let mockAuthState: MockAuthState = defaultAuthState

// Function to update mock state from tests
export const setMockAuthState = (newState: Partial<MockAuthState>) => {
  mockAuthState = { ...mockAuthState, ...newState }
}

// Function to reset mock state
export const resetMockAuthState = () => {
  mockAuthState = defaultAuthState
}

// Mock AuthGuard component that always renders children
const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // In test environment, always render children without authentication checks
  return <>{children}</>
}

// Mock useAuth hook that doesn't trigger navigation loops
export const useAuth = () => {
  return {
    ...mockAuthState,
    login: jest.fn().mockResolvedValue(undefined),
    logout: jest.fn().mockResolvedValue(undefined),
    hasRole: jest.fn((role: string) => {
      if (!mockAuthState.user) return false
      return mockAuthState.user.role === role
    }),
    hasAnyRole: jest.fn((roles: string[]) => {
      if (!mockAuthState.user) return false
      return roles.includes(mockAuthState.user.role)
    }),
    hasPermission: jest.fn((permission: string) => {
      if (!mockAuthState.user) return false
      return mockAuthState.user.permissions?.includes(permission) || false
    }),
    hasAnyPermission: jest.fn((permissions: string[]) => {
      if (!mockAuthState.user) return false
      return permissions.some(p => mockAuthState.user.permissions?.includes(p))
    }),
    hasAllPermissions: jest.fn((permissions: string[]) => {
      if (!mockAuthState.user) return false
      return permissions.every(p => mockAuthState.user.permissions?.includes(p))
    }),
    isAdmin: jest.fn(() => mockAuthState.user?.role === 'ADMIN'),
    isFinance: jest.fn(() => mockAuthState.user?.role === 'FINANCE'),
    refreshToken: jest.fn().mockResolvedValue(undefined),
    updatePermissions: jest.fn().mockResolvedValue(undefined)
  }
}

// Mock withAuthGuard HOC
export const withAuthGuard = (Component: React.ComponentType<any>) => {
  return (props: any) => <Component {...props} />
}

export default AuthGuard