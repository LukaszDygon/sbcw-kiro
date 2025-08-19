/**
 * AuthGuard component tests
 * Tests the isolated testing approach for authentication-dependent components
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import AuthGuard, { useAuth, setMockAuthState, resetMockAuthState } from '../AuthGuard'

// Mock user data for testing
const mockUser = {
  id: 'test-user-id',
  name: 'Test User',
  email: 'test@example.com',
  role: 'EMPLOYEE',
  permissions: ['read', 'write'],
  microsoft_id: 'test-microsoft-id'
}

const loadingAuthState = {
  isAuthenticated: false,
  isInitialized: false,
  isLoading: true,
  user: null,
  error: null
}

const unauthenticatedAuthState = {
  isAuthenticated: false,
  isInitialized: true,
  isLoading: false,
  user: null,
  error: null
}

const errorAuthState = {
  isAuthenticated: false,
  isInitialized: true,
  isLoading: false,
  user: null,
  error: 'Authentication failed'
}

// Test component that uses useAuth hook
const TestComponent: React.FC = () => {
  const { user, isAuthenticated, isLoading, error } = useAuth()
  
  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>
  if (!isAuthenticated) return <div>Not authenticated</div>
  
  return <div>Hello {user?.name}</div>
}

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('AuthGuard Component', () => {
  beforeEach(() => {
    resetMockAuthState()
  })

  it('renders children when authenticated', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    })

    renderWithRouter(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>
    )

    expect(screen.getByText('Protected content')).toBeInTheDocument()
  })

  it('renders children without authentication checks in test environment', () => {
    // Even with unauthenticated state, mock should render children
    setMockAuthState(unauthenticatedAuthState)

    renderWithRouter(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>
    )

    // In test environment, AuthGuard mock always renders children
    expect(screen.getByText('Protected content')).toBeInTheDocument()
  })

  it('does not cause infinite loops during testing', () => {
    setMockAuthState(loadingAuthState)

    renderWithRouter(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>
    )

    // Should render immediately without getting stuck in loading state
    expect(screen.getByText('Protected content')).toBeInTheDocument()
  })
})

describe('useAuth Hook', () => {
  beforeEach(() => {
    resetMockAuthState()
  })

  it('returns authenticated state', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    })

    render(<TestComponent />)
    expect(screen.getByText('Hello Test User')).toBeInTheDocument()
  })

  it('returns loading state', () => {
    setMockAuthState(loadingAuthState)

    render(<TestComponent />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('returns unauthenticated state', () => {
    setMockAuthState(unauthenticatedAuthState)

    render(<TestComponent />)
    expect(screen.getByText('Not authenticated')).toBeInTheDocument()
  })

  it('returns error state', () => {
    setMockAuthState(errorAuthState)

    render(<TestComponent />)
    expect(screen.getByText('Error: Authentication failed')).toBeInTheDocument()
  })

  it('provides role checking functions', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: { ...mockUser, role: 'ADMIN' },
      error: null
    })

    const TestRoleComponent: React.FC = () => {
      const { hasRole, isAdmin } = useAuth()
      return (
        <div>
          <div>Has admin role: {hasRole('ADMIN') ? 'yes' : 'no'}</div>
          <div>Is admin: {isAdmin() ? 'yes' : 'no'}</div>
        </div>
      )
    }

    render(<TestRoleComponent />)
    expect(screen.getByText('Has admin role: yes')).toBeInTheDocument()
    expect(screen.getByText('Is admin: yes')).toBeInTheDocument()
  })

  it('provides permission checking functions', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: { ...mockUser, permissions: ['read', 'write'] },
      error: null
    })

    const TestPermissionComponent: React.FC = () => {
      const { hasPermission, hasAnyPermission } = useAuth()
      return (
        <div>
          <div>Has read: {hasPermission('read') ? 'yes' : 'no'}</div>
          <div>Has any: {hasAnyPermission(['read', 'admin']) ? 'yes' : 'no'}</div>
        </div>
      )
    }

    render(<TestPermissionComponent />)
    expect(screen.getByText('Has read: yes')).toBeInTheDocument()
    expect(screen.getByText('Has any: yes')).toBeInTheDocument()
  })

  it('does not trigger navigation loops in test environment', () => {
    // This test ensures that the mock doesn't cause infinite re-renders
    let renderCount = 0
    
    const TestRenderCountComponent: React.FC = () => {
      renderCount++
      const { user } = useAuth()
      return <div>Render count: {renderCount}, User: {user?.name}</div>
    }

    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    })

    render(<TestRenderCountComponent />)
    
    // Should only render once, not cause infinite loops
    expect(renderCount).toBe(1)
    expect(screen.getByText('Render count: 1, User: Test User')).toBeInTheDocument()
  })
})