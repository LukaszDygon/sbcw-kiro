/**
 * Admin service for user management and system configuration
 */
import api from './api'

export interface User {
  id: string
  microsoft_id: string
  email: string
  name: string
  role: 'EMPLOYEE' | 'ADMIN' | 'FINANCE'
  account_status: 'ACTIVE' | 'SUSPENDED' | 'CLOSED'
  created_at: string
  last_login: string | null
  account: {
    balance: string
    created_at: string | null
  }
}

export interface UserDetails extends User {
  recent_transactions: Array<{
    id: string
    amount: string
    type: 'sent' | 'received'
    other_party: string
    created_at: string
    status: string
  }>
  recent_activity: Array<{
    id: string
    action_type: string
    created_at: string
    details?: any
  }>
}

export interface UsersResponse {
  users: User[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
    has_next: boolean
    has_prev: boolean
  }
}

export interface SystemConfig {
  application: {
    name: string
    version: string
    environment: string
  }
  features: {
    microsoft_sso_enabled: boolean
    audit_logging_enabled: boolean
    reporting_enabled: boolean
    rate_limiting_enabled: boolean
  }
  limits: {
    max_account_balance: string
    min_account_balance: string
    max_transaction_amount: string
    session_timeout_hours: number
  }
  security: {
    password_policy_enabled: boolean
    two_factor_enabled: boolean
    audit_retention_days: number
    session_encryption: boolean
  }
}

export interface MaintenanceResult {
  task: string
  success: boolean
  message: string
  details: any
}

export const adminService = {
  /**
   * Get all users with filtering and pagination
   */
  async getUsers(params?: {
    role?: string
    status?: string
    search?: string
    page?: number
    per_page?: number
  }): Promise<UsersResponse> {
    const searchParams = new URLSearchParams()
    
    if (params?.role) searchParams.append('role', params.role)
    if (params?.status) searchParams.append('status', params.status)
    if (params?.search) searchParams.append('search', params.search)
    if (params?.page) searchParams.append('page', params.page.toString())
    if (params?.per_page) searchParams.append('per_page', params.per_page.toString())
    
    const response = await api.get(`/admin/users?${searchParams.toString()}`)
    return response.data
  },

  /**
   * Get detailed user information
   */
  async getUserDetails(userId: string): Promise<UserDetails> {
    const response = await api.get(`/admin/users/${userId}`)
    return response.data
  },

  /**
   * Update user account status
   */
  async updateUserStatus(userId: string, status: string, reason?: string): Promise<{ message: string; user: User }> {
    const response = await api.put(`/admin/users/${userId}/status`, {
      status,
      reason
    })
    return response.data
  },

  /**
   * Update user role
   */
  async updateUserRole(userId: string, role: string, reason?: string): Promise<{ message: string; user: User }> {
    const response = await api.put(`/admin/users/${userId}/role`, {
      role,
      reason
    })
    return response.data
  },

  /**
   * Get system configuration
   */
  async getSystemConfig(): Promise<SystemConfig> {
    const response = await api.get('/admin/system/config')
    return response.data
  },

  /**
   * Perform system maintenance task
   */
  async performMaintenance(task: string, parameters?: any): Promise<MaintenanceResult> {
    const response = await api.post('/admin/system/maintenance', {
      task,
      parameters
    })
    return response.data
  }
}