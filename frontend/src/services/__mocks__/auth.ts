// Mock auth service for testing
export enum AuthState {
  LOADING = 'loading',
  AUTHENTICATED = 'authenticated',
  UNAUTHENTICATED = 'unauthenticated',
  ERROR = 'error'
}

export enum AuthEventType {
  LOGIN_SUCCESS = 'login_success',
  LOGIN_FAILURE = 'login_failure',
  LOGOUT = 'logout',
  TOKEN_REFRESH = 'token_refresh',
  SESSION_EXPIRED = 'session_expired'
}

// Create mock functions that can be used in tests
export const getState = jest.fn()
export const getUser = jest.fn()
export const login = jest.fn()
export const logout = jest.fn()
export const refreshToken = jest.fn()
export const isAuthenticated = jest.fn()
export const getToken = jest.fn()
export const subscribe = jest.fn()
export const getCurrentUser = jest.fn()
export const getAuthState = jest.fn()
export const addEventListener = jest.fn()
export const removeEventListener = jest.fn()
export const initialize = jest.fn()
export const hasAnyRole = jest.fn()
export const hasAllPermissions = jest.fn()
export const hasAnyPermission = jest.fn()
export const loginWithMicrosoft = jest.fn()
export const hasRole = jest.fn()
export const hasPermission = jest.fn()
export const isAdmin = jest.fn()
export const isFinance = jest.fn()
export const forceRefreshToken = jest.fn()
export const updatePermissions = jest.fn()

// Set up default mock implementations
let mockAuthState = {
  isAuthenticated: false,
  isInitialized: false,
  user: null,
  error: null
}

getAuthState.mockImplementation(() => mockAuthState)
isAuthenticated.mockImplementation(() => mockAuthState.isAuthenticated)
getCurrentUser.mockImplementation(() => Promise.resolve(mockAuthState.user))
initialize.mockImplementation(() => {
  mockAuthState = { ...mockAuthState, isInitialized: true }
  return Promise.resolve(mockAuthState.user)
})

// Set up default implementations for role/permission methods
hasAnyRole.mockReturnValue(true)
hasAllPermissions.mockReturnValue(true)
hasAnyPermission.mockReturnValue(true)
hasRole.mockReturnValue(true)
hasPermission.mockReturnValue(true)
isAdmin.mockReturnValue(false)
isFinance.mockReturnValue(false)

// Helper function to update mock state
export const setMockAuthState = (newState: Partial<typeof mockAuthState>) => {
  mockAuthState = { ...mockAuthState, ...newState }
}

const mockAuthService = {
  getState,
  getUser,
  login,
  logout,
  refreshToken,
  isAuthenticated,
  getToken,
  subscribe,
  getCurrentUser,
  getAuthState,
  addEventListener,
  removeEventListener,
  initialize,
  hasAnyRole,
  hasAllPermissions,
  hasAnyPermission,
  loginWithMicrosoft,
  hasRole,
  hasPermission,
  isAdmin,
  isFinance,
  forceRefreshToken,
  updatePermissions,
  setMockAuthState,
}

export default mockAuthService