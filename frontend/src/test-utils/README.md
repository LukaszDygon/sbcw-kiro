# AuthGuard Testing Utilities

This directory contains utilities for testing authentication-dependent components without infinite loops or navigation conflicts.

## Problem Solved

The original AuthGuard component caused infinite loops during testing because:
1. It would initialize authentication on mount
2. The real auth service would try to make API calls
3. Navigation would be triggered during test rendering
4. Components would get stuck in loading states

## Solution

### 1. AuthGuard Mock (`frontend/src/components/__mocks__/AuthGuard.tsx`)

- **Prevents infinite loops**: Always renders children without authentication checks in test environment
- **Controllable state**: Provides `setMockAuthState` and `resetMockAuthState` functions
- **No navigation side effects**: Doesn't trigger React Router navigation during tests
- **Complete API**: Mocks all authentication methods (hasRole, hasPermission, etc.)

### 2. Test Utilities (`frontend/src/test-utils/auth-test-utils.tsx`)

- **TestWrapper**: Provides all necessary context (QueryClient, Router, Accessibility)
- **Mock user data**: Predefined user objects for different roles
- **Auth state presets**: Common authentication states (loading, authenticated, error)
- **Isolated testing**: Components can be tested without real authentication flow

### 3. Service Mocks (Updated)

- **Consistent structure**: All service mocks now match the actual service exports
- **Proper Jest mocking**: Uses jest.fn() for all methods
- **Backward compatibility**: Exports both object and individual functions

## Usage

### Basic Component Test

```typescript
import { render, screen } from '@testing-library/react'
import { TestWrapper } from '../../test-utils/auth-test-utils'
import { setMockAuthState, resetMockAuthState } from '../__mocks__/AuthGuard'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  beforeEach(() => {
    resetMockAuthState()
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    })
  })

  it('renders without infinite loops', () => {
    render(
      <TestWrapper>
        <MyComponent />
      </TestWrapper>
    )
    
    expect(screen.getByText('My Component')).toBeInTheDocument()
  })
})
```

### Testing Different Auth States

```typescript
// Test loading state
setMockAuthState({
  isAuthenticated: false,
  isInitialized: false,
  isLoading: true,
  user: null,
  error: null
})

// Test error state
setMockAuthState({
  isAuthenticated: false,
  isInitialized: true,
  isLoading: false,
  user: null,
  error: 'Authentication failed'
})

// Test admin user
setMockAuthState({
  isAuthenticated: true,
  isInitialized: true,
  isLoading: false,
  user: { ...mockUser, role: 'ADMIN' },
  error: null
})
```

## Key Benefits

1. **No infinite loops**: Components render immediately without getting stuck
2. **No navigation conflicts**: Tests don't trigger React Router navigation
3. **Isolated testing**: Each test can control authentication state independently
4. **Fast execution**: No real API calls or authentication flows
5. **Comprehensive coverage**: Can test all authentication scenarios

## Files Created/Modified

- `frontend/src/components/__mocks__/AuthGuard.tsx` - Mock AuthGuard component
- `frontend/src/test-utils/auth-test-utils.tsx` - Testing utilities
- `frontend/src/services/__mocks__/*.ts` - Updated service mocks
- `frontend/src/setupTests.ts` - Added AuthGuard mock configuration
- `frontend/src/components/__tests__/AuthGuard.test.tsx` - AuthGuard tests
- `frontend/src/components/__tests__/SendMoney.simplified.test.tsx` - Example usage

## Task Requirements Completed

✅ **Resolve infinite loop issues in AuthGuard component during testing**
✅ **Create simplified mock for useAuth hook that doesn't trigger navigation loops**  
✅ **Implement isolated testing approach for authentication-dependent components**
✅ **Fix React Router navigation conflicts in test environment**
✅ **Create test utilities for mocking authentication state without side effects**

The solution successfully prevents infinite loops while maintaining full testing capability for authentication-dependent components.