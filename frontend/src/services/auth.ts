/**
 * Enhanced Authentication service for SoftBankCashWire frontend
 * Handles Microsoft SSO authentication, JWT token management, and session security
 */
// Mock MSAL types for development
interface Configuration {
  auth: {
    clientId: string
    authority: string
    redirectUri: string
  }
  cache: {
    cacheLocation: string
    storeAuthStateInCookie: boolean
  }
}

interface AuthenticationResult {
  accessToken?: string
}

interface PublicClientApplication {
  initialize(): Promise<void>
  loginPopup(request: any): Promise<AuthenticationResult>
  logoutPopup(): Promise<void>
}

// Mock MSAL implementation for development
const createMockMsalInstance = (): PublicClientApplication => ({
  initialize: async () => {},
  loginPopup: async () => ({ accessToken: 'mock-token' }),
  logoutPopup: async () => {}
})
import apiClient, { handleApiError } from './api'
import { User, ApiError } from '../types'

// Microsoft MSAL configuration
const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_MICROSOFT_CLIENT_ID || '',
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_MICROSOFT_TENANT_ID || 'common'}`,
    redirectUri: window.location.origin + '/auth/callback',
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
}

// Create MSAL instance (mock for development)
const msalInstance = createMockMsalInstance()

// Initialize MSAL
msalInstance.initialize().catch(console.error)

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
  expires_in: number
  permissions?: string[]
  session_id?: string
}

export interface LoginUrlResponse {
  login_url: string
  state: string
  redirect_uri: string
}

export interface SessionInfo {
  session_id: string
  expires_at: string
  ip_address: string
  user_agent: string
  last_activity: string
}

export interface AuthState {
  isAuthenticated: boolean
  isLoading: boolean
  user: User | null
  permissions: string[]
  error: string | null
  sessionInfo: SessionInfo | null
}

export type AuthEventType = 'login' | 'logout' | 'token_refresh' | 'session_expired' | 'permission_changed'

export interface AuthEventListener {
  (event: AuthEventType, data?: any): void
}

class AuthService {
  private static refreshTimer: NodeJS.Timeout | null = null
  private static sessionCheckTimer: NodeJS.Timeout | null = null
  private static eventListeners: Map<AuthEventType, AuthEventListener[]> = new Map()
  private static authState: AuthState = {
    isAuthenticated: false,
    isLoading: false,
    user: null,
    permissions: [],
    error: null,
    sessionInfo: null
  }
  /**
   * Get Microsoft OAuth login URL from backend
   */
  static async getLoginUrl(redirectUri?: string): Promise<LoginUrlResponse> {
    try {
      const params = new URLSearchParams()
      if (redirectUri) {
        params.append('redirect_uri', redirectUri)
      }

      const response = await apiClient.get(`/auth/login-url?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Initiate Microsoft SSO login using MSAL
   */
  static async loginWithMicrosoft(): Promise<AuthResponse> {
    try {
      this.setLoading(true)
      this.setError(null)

      // Request Microsoft Graph access token
      const loginRequest = {
        scopes: ['User.Read'],
        prompt: 'select_account',
      }

      const result: AuthenticationResult = await msalInstance.loginPopup(loginRequest)
      
      if (!result.accessToken) {
        throw new Error('No access token received from Microsoft')
      }

      // Authenticate with backend using Microsoft token
      const response = await apiClient.post('/auth/token', {
        access_token: result.accessToken,
      })

      const authData: AuthResponse = response.data

      // Store tokens and user info
      this.storeAuthData(authData)
      this.emitEvent('login', authData.user)

      return authData
    } catch (error) {
      this.setError('Microsoft login failed')
      throw handleApiError(error)
    } finally {
      this.setLoading(false)
    }
  }

  /**
   * Handle OAuth callback with authorization code
   */
  static async handleCallback(code: string, redirectUri: string, state?: string): Promise<AuthResponse> {
    try {
      this.setLoading(true)
      this.setError(null)

      const response = await apiClient.post('/auth/callback', {
        code,
        redirect_uri: redirectUri,
        state,
      })

      const authData: AuthResponse = response.data

      // Store tokens and user info
      this.storeAuthData(authData)
      this.emitEvent('login', authData.user)

      return authData
    } catch (error) {
      this.setError('Authentication callback failed')
      throw handleApiError(error)
    } finally {
      this.setLoading(false)
    }
  }

  /**
   * Refresh access token
   */
  static async refreshToken(): Promise<{ access_token: string; expires_in: number }> {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      const response = await apiClient.post('/auth/refresh', {}, {
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
      })

      const tokenData = response.data
      localStorage.setItem('access_token', tokenData.access_token)

      return tokenData
    } catch (error) {
      // If refresh fails, clear stored data and redirect to login
      this.logout()
      throw handleApiError(error)
    }
  }

  /**
   * Get current user information
   */
  static async getCurrentUser(): Promise<{ user: User; permissions: Record<string, boolean> }> {
    try {
      const response = await apiClient.get('/auth/me')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Validate current token
   */
  static async validateToken(): Promise<{ valid: boolean; user_id: string; email: string; role: string }> {
    try {
      const response = await apiClient.get('/auth/validate')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get user permissions
   */
  static async getUserPermissions(): Promise<{ permissions: Record<string, boolean> }> {
    try {
      const response = await apiClient.get('/auth/permissions')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Logout user
   */
  static async logout(): Promise<void> {
    try {
      this.setLoading(true)
      // Call backend logout endpoint
      await apiClient.post('/auth/logout')
    } catch (error) {
      // Continue with logout even if backend call fails
      console.warn('Backend logout failed:', error)
    } finally {
      // Clear local storage
      this.clearAuthData()
      this.emitEvent('logout')

      // Logout from MSAL
      try {
        await msalInstance.logoutPopup()
      } catch (msalError) {
        console.warn('MSAL logout failed:', msalError)
      }

      this.setLoading(false)
      // Redirect to login page
      window.location.href = '/login'
    }
  }

  /**
   * Check if user is authenticated
   */
  static isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token')
    const user = localStorage.getItem('user')
    return !!(token && user)
  }

  /**
   * Get stored user data
   */
  static getStoredUser(): User | null {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        return JSON.parse(userStr)
      } catch {
        return null
      }
    }
    return null
  }

  /**
   * Get stored access token
   */
  static getAccessToken(): string | null {
    return localStorage.getItem('access_token')
  }

  /**
   * Store authentication data
   */
  private static storeAuthData(authData: AuthResponse): void {
    localStorage.setItem('access_token', authData.access_token)
    localStorage.setItem('refresh_token', authData.refresh_token)
    localStorage.setItem('user', JSON.stringify(authData.user))

    // Store permissions if provided
    if (authData.permissions) {
      localStorage.setItem('permissions', JSON.stringify(authData.permissions))
      this.authState.permissions = authData.permissions
    }

    // Store session info if provided
    if (authData.session_id) {
      const sessionInfo: SessionInfo = {
        session_id: authData.session_id,
        expires_at: new Date(Date.now() + authData.expires_in * 1000).toISOString(),
        ip_address: '', // Will be filled by session check
        user_agent: navigator.userAgent,
        last_activity: new Date().toISOString()
      }
      localStorage.setItem('session_info', JSON.stringify(sessionInfo))
      this.authState.sessionInfo = sessionInfo
    }

    // Set token expiration time
    const expirationTime = Date.now() + (authData.expires_in * 1000)
    localStorage.setItem('token_expiration', expirationTime.toString())
    localStorage.setItem('token_issued_at', Date.now().toString())

    // Update auth state
    this.authState.isAuthenticated = true
    this.authState.user = authData.user
    this.authState.error = null

    // Start token refresh and session monitoring
    this.startTokenRefresh(authData.expires_in)
    this.startSessionMonitoring()
  }

  /**
   * Clear stored authentication data
   */
  private static clearAuthData(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('token_expiration')
    localStorage.removeItem('token_issued_at')
    localStorage.removeItem('permissions')
    localStorage.removeItem('session_info')
    localStorage.removeItem('csrf_token')

    // Clear timers
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
      this.refreshTimer = null
    }
    
    if (this.sessionCheckTimer) {
      clearTimeout(this.sessionCheckTimer)
      this.sessionCheckTimer = null
    }

    // Reset auth state
    this.authState = {
      isAuthenticated: false,
      isLoading: false,
      user: null,
      permissions: [],
      error: null,
      sessionInfo: null
    }
  }

  /**
   * Check if token is expired
   */
  static isTokenExpired(): boolean {
    const expirationTime = localStorage.getItem('token_expiration')
    if (!expirationTime) {
      return true
    }

    return Date.now() > parseInt(expirationTime)
  }

  /**
   * Check if user has specific permission
   */
  static async hasPermission(permission: string): Promise<boolean> {
    try {
      const { permissions } = await this.getUserPermissions()
      return permissions[permission] || false
    } catch {
      return false
    }
  }

  /**
   * Check if user has specific role
   */
  static hasRole(role: string): boolean {
    const user = this.getStoredUser()
    return user?.role === role
  }

  /**
   * Check if user is admin
   */
  static isAdmin(): boolean {
    return this.hasRole('ADMIN') || this.hasRole('FINANCE')
  }

  /**
   * Check if user is finance team member
   */
  static isFinance(): boolean {
    return this.hasRole('FINANCE')
  }

  /**
   * Get current auth state
   */
  static getAuthState(): AuthState {
    return { ...this.authState }
  }

  /**
   * Set loading state
   */
  static setLoading(loading: boolean): void {
    this.authState.isLoading = loading
  }

  /**
   * Set error state
   */
  static setError(error: string | null): void {
    this.authState.error = error
  }

  /**
   * Get session information
   */
  static getSessionInfo(): SessionInfo | null {
    if (this.authState.sessionInfo) {
      return this.authState.sessionInfo
    }
    
    const sessionStr = localStorage.getItem('session_info')
    const sessionInfo = sessionStr ? JSON.parse(sessionStr) : null
    this.authState.sessionInfo = sessionInfo
    return sessionInfo
  }

  /**
   * Get stored permissions
   */
  static getStoredPermissions(): string[] {
    if (this.authState.permissions.length > 0) {
      return this.authState.permissions
    }
    
    const permissionsStr = localStorage.getItem('permissions')
    const permissions = permissionsStr ? JSON.parse(permissionsStr) : []
    this.authState.permissions = permissions
    return permissions
  }

  /**
   * Check if user has any of the specified permissions
   */
  static hasAnyPermission(permissions: string[]): boolean {
    const userPermissions = this.getStoredPermissions()
    return permissions.some(permission => userPermissions.includes(permission))
  }

  /**
   * Check if user has all specified permissions
   */
  static hasAllPermissions(permissions: string[]): boolean {
    const userPermissions = this.getStoredPermissions()
    return permissions.every(permission => userPermissions.includes(permission))
  }

  /**
   * Check if user has any of the specified roles
   */
  static hasAnyRole(roles: string[]): boolean {
    const user = this.getStoredUser()
    return user ? roles.includes(user.role) : false
  }

  /**
   * Add event listener
   */
  static addEventListener(event: AuthEventType, listener: AuthEventListener): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, [])
    }
    this.eventListeners.get(event)!.push(listener)
  }

  /**
   * Remove event listener
   */
  static removeEventListener(event: AuthEventType, listener: AuthEventListener): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  /**
   * Emit authentication event
   */
  private static emitEvent(event: AuthEventType, data?: any): void {
    const listeners = this.eventListeners.get(event)
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(event, data)
        } catch (error) {
          console.error(`Error in auth event listener for ${event}:`, error)
        }
      })
    }
  }

  /**
   * Initialize authentication on app start
   */
  static async initialize(): Promise<User | null> {
    try {
      this.setLoading(true)
      
      if (!this.isAuthenticated()) {
        return null
      }

      // Validate token and session
      const [isTokenValid, isSessionValid] = await Promise.all([
        this.validateToken().then(() => true).catch(() => false),
        this.checkSession()
      ])

      if (!isTokenValid || !isSessionValid) {
        this.clearAuthData()
        return null
      }

      const user = this.getStoredUser()
      if (user) {
        this.authState.isAuthenticated = true
        this.authState.user = user
        this.authState.permissions = this.getStoredPermissions()
        this.authState.sessionInfo = this.getSessionInfo()

        // Start monitoring
        const expirationTime = localStorage.getItem('token_expiration')
        if (expirationTime) {
          const expiresIn = Math.max(0, (parseInt(expirationTime) - Date.now()) / 1000)
          this.startTokenRefresh(expiresIn)
        }
        this.startSessionMonitoring()
      }

      return user
    } catch (error) {
      console.error('Auth initialization failed:', error)
      this.clearAuthData()
      return null
    } finally {
      this.setLoading(false)
    }
  }

  /**
   * Check session status
   */
  static async checkSession(): Promise<boolean> {
    try {
      const response = await apiClient.get('/auth/session')
      
      if (response.data.valid && response.data.session) {
        localStorage.setItem('session_info', JSON.stringify(response.data.session))
        this.authState.sessionInfo = response.data.session
        return true
      }
      
      return false
    } catch (error) {
      console.error('Session check failed:', error)
      return false
    }
  }

  /**
   * Start automatic token refresh
   */
  private static startTokenRefresh(expiresIn: number): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
    }

    // Refresh token 5 minutes before expiry
    const refreshTime = Math.max((expiresIn - 300) * 1000, 60000) // At least 1 minute

    this.refreshTimer = setTimeout(async () => {
      try {
        await this.refreshToken()
        this.emitEvent('token_refresh')
      } catch (error) {
        console.error('Automatic token refresh failed:', error)
        this.handleSessionExpired()
      }
    }, refreshTime)
  }

  /**
   * Start session monitoring
   */
  private static startSessionMonitoring(): void {
    if (this.sessionCheckTimer) {
      clearTimeout(this.sessionCheckTimer)
    }

    // Check session every 5 minutes
    this.sessionCheckTimer = setTimeout(async () => {
      try {
        const isValid = await this.checkSession()
        if (!isValid) {
          this.handleSessionExpired()
        } else {
          this.startSessionMonitoring() // Continue monitoring
        }
      } catch (error) {
        console.error('Session monitoring failed:', error)
        this.handleSessionExpired()
      }
    }, 5 * 60 * 1000) // 5 minutes
  }

  /**
   * Handle session expiration
   */
  private static handleSessionExpired(): void {
    this.clearAuthData()
    this.emitEvent('session_expired')
    
    // Redirect to login if not already there
    if (window.location.pathname !== '/login') {
      window.location.href = '/login?reason=session_expired'
    }
  }

  /**
   * Force token refresh
   */
  static async forceRefreshToken(): Promise<void> {
    // Set issued_at to 0 to force refresh
    localStorage.setItem('token_issued_at', '0')
    await this.refreshToken()
  }

  /**
   * Update user permissions
   */
  static async updatePermissions(): Promise<string[]> {
    try {
      const response = await apiClient.get('/auth/permissions')
      const permissions = response.data.permissions || []
      localStorage.setItem('permissions', JSON.stringify(permissions))
      this.authState.permissions = permissions
      this.emitEvent('permission_changed', permissions)
      return permissions
    } catch (error) {
      console.error('Error updating permissions:', error)
      throw handleApiError(error)
    }
  }

  /**
   * Get CSRF token
   */
  static getCSRFToken(): string | null {
    return localStorage.getItem('csrf_token')
  }

  /**
   * Set CSRF token
   */
  static setCSRFToken(token: string): void {
    localStorage.setItem('csrf_token', token)
  }

  /**
   * Search users by name or email
   */
  static async searchUsers(
    searchTerm: string, 
    options: { limit?: number; exclude_self?: boolean } = {}
  ): Promise<{ users: Array<{ id: string; name: string; email: string; role: string }>; search_term: string; count: number }> {
    try {
      const params = new URLSearchParams({
        q: searchTerm,
        limit: (options.limit || 10).toString(),
        exclude_self: (options.exclude_self !== false).toString()
      })
      
      const response = await apiClient.get(`/auth/users/search?${params}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }
}

export default AuthService

// Export as authService for backward compatibility
export const authService = AuthService
