/**
 * Test utilities for mocking authentication state without side effects
 * Provides isolated testing approach for authentication-dependent components
 */
import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { AccessibilityProvider } from '../contexts/AccessibilityContext'

// Mock user data for testing
export const mockUser = {
  id: 'test-user-id',
  name: 'Test User',
  email: 'test@example.com',
  role: 'EMPLOYEE',
  permissions: ['read', 'write'],
  microsoft_id: 'test-microsoft-id'
}

export const mockAdminUser = {
  ...mockUser,
  role: 'ADMIN',
  permissions: ['read', 'write', 'admin']
}

export const mockFinanceUser = {
  ...mockUser,
  role: 'FINANCE',
  permissions: ['read', 'write', 'finance']
}

// Simplified auth state interface for testing
export interface MockAuthState {
  isAuthenticated: boolean
  isInitialized: boolean
  isLoading: boolean
  user: any | null
  error: string | null
}

// Default authenticated state
export const defaultAuthState: MockAuthState = {
  isAuthenticated: true,
  isInitialized: true,
  isLoading: false,
  user: mockUser,
  error: null
}

// Loading state
export const loadingAuthState: MockAuthState = {
  isAuthenticated: false,
  isInitialized: false,
  isLoading: true,
  user: null,
  error: null
}

// Unauthenticated state
export const unauthenticatedAuthState: MockAuthState = {
  isAuthenticated: false,
  isInitialized: true,
  isLoading: false,
  user: null,
  error: null
}

// Error state
export const errorAuthState: MockAuthState = {
  isAuthenticated: false,
  isInitialized: true,
  isLoading: false,
  user: null,
  error: 'Authentication failed'
}

// Create a mock useAuth hook that doesn't trigger navigation loops
export const createMockUseAuth = (authState: MockAuthState = defaultAuthState) => {
  return jest.fn(() => ({
    ...authState,
    login: jest.fn().mockResolvedValue(undefined),
    logout: jest.fn().mockResolvedValue(undefined),
    hasRole: jest.fn().mockReturnValue(true),
    hasAnyRole: jest.fn().mockReturnValue(true),
    hasPermission: jest.fn().mockReturnValue(true),
    hasAnyPermission: jest.fn().mockReturnValue(true),
    hasAllPermissions: jest.fn().mockReturnValue(true),
    isAdmin: jest.fn().mockReturnValue(authState.user?.role === 'ADMIN'),
    isFinance: jest.fn().mockReturnValue(authState.user?.role === 'FINANCE'),
    refreshToken: jest.fn().mockResolvedValue(undefined),
    updatePermissions: jest.fn().mockResolvedValue(undefined)
  }))
}

// Test wrapper component that provides all necessary context
export const TestWrapper: React.FC<{ 
  children: React.ReactNode
  queryClient?: QueryClient
}> = ({ children, queryClient }) => {
  const client = queryClient || new QueryClient({
    defaultOptions: {
      queries: { 
        retry: false,
        cacheTime: 0,
        staleTime: 0
      },
      mutations: { retry: false },
    },
  })

  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <AccessibilityProvider>
          {children}
        </AccessibilityProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

// Wrapper for components that need authentication but should bypass AuthGuard
export const AuthenticatedTestWrapper: React.FC<{ 
  children: React.ReactNode
  authState?: MockAuthState
  queryClient?: QueryClient
}> = ({ children, authState = defaultAuthState, queryClient }) => {
  // Mock the useAuth hook for this test context
  const mockUseAuth = createMockUseAuth(authState)
  
  // Replace the useAuth import in the component being tested
  jest.doMock('../components/AuthGuard', () => ({
    useAuth: mockUseAuth,
    default: ({ children }: { children: React.ReactNode }) => <>{children}</>
  }))

  return (
    <TestWrapper queryClient={queryClient}>
      {children}
    </TestWrapper>
  )
}

// Utility to mock AuthGuard to always render children without authentication checks
export const mockAuthGuard = () => {
  jest.doMock('../components/AuthGuard', () => ({
    useAuth: createMockUseAuth(),
    default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    withAuthGuard: (Component: React.ComponentType<any>) => Component
  }))
}

// Utility to reset auth mocks
export const resetAuthMocks = () => {
  jest.clearAllMocks()
  jest.resetModules()
}

// Helper to create isolated component tests without navigation side effects
export const renderWithAuth = (
  component: React.ReactElement,
  options: {
    authState?: MockAuthState
    queryClient?: QueryClient
  } = {}
) => {
  const { authState = defaultAuthState, queryClient } = options
  
  return (
    <AuthenticatedTestWrapper authState={authState} queryClient={queryClient}>
      {component}
    </AuthenticatedTestWrapper>
  )
}