/**
 * Money Request service for SoftBankCashWire frontend
 */
import apiClient, { handleApiError } from './api'
import { MoneyRequest, RequestStatus, Transaction } from '../types'

export interface CreateMoneyRequestRequest {
  recipient_id: string
  amount: string
  note?: string
  expires_in_days?: number
}

export interface CreateMoneyRequestResult {
  success: boolean
  request: MoneyRequest
  expires_in_hours: number
}

export interface RespondToRequestRequest {
  approved: boolean
}

export interface RespondToRequestResult {
  success: boolean
  approved: boolean
  request: MoneyRequest
  transaction?: Transaction
  sender_balance?: string
  recipient_balance?: string
  message?: string
}

export interface CancelRequestResult {
  success: boolean
  request: MoneyRequest
  message: string
}

export interface MoneyRequestList {
  requests: MoneyRequest[]
  pagination?: {
    total: number
    limit: number
    offset: number
    has_more: boolean
  }
  count?: number
}

export interface MoneyRequestStatistics {
  period_days: number
  sent_requests: {
    total: number
    approved: number
    declined: number
    pending: number
    expired: number
    approval_rate: number
    total_amount_approved: string
  }
  received_requests: {
    total: number
    approved: number
    declined: number
    pending: number
    expired: number
    approval_rate: number
    total_amount_approved: string
  }
}

export interface RequestValidationResult {
  valid: boolean
  errors: Array<{
    code: string
    message: string
  }>
  warnings: Array<{
    code: string
    message: string
  }>
}

export interface ExpiringRequestsResult {
  requests: MoneyRequest[]
  count: number
  hours_threshold: number
}

class MoneyRequestsService {
  /**
   * Create a new money request
   */
  static async createMoneyRequest(request: CreateMoneyRequestRequest): Promise<CreateMoneyRequestResult> {
    try {
      const response = await apiClient.post('/money-requests/create', request)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Respond to a money request (approve or decline)
   */
  static async respondToRequest(requestId: string, approved: boolean): Promise<RespondToRequestResult> {
    try {
      const response = await apiClient.post(`/money-requests/${requestId}/respond`, {
        approved
      })
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Cancel a money request
   */
  static async cancelRequest(requestId: string): Promise<CancelRequestResult> {
    try {
      const response = await apiClient.post(`/money-requests/${requestId}/cancel`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get money request details by ID
   */
  static async getRequest(requestId: string): Promise<{ request: MoneyRequest }> {
    try {
      const response = await apiClient.get(`/money-requests/${requestId}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get pending money requests (as recipient)
   */
  static async getPendingRequests(): Promise<MoneyRequestList> {
    try {
      const response = await apiClient.get('/money-requests/pending')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get sent money requests
   */
  static async getSentRequests(
    status?: RequestStatus,
    limit: number = 50,
    offset: number = 0
  ): Promise<MoneyRequestList> {
    try {
      const params = new URLSearchParams()
      if (status) params.append('status', status)
      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      const response = await apiClient.get(`/money-requests/sent?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get received money requests
   */
  static async getReceivedRequests(
    status?: RequestStatus,
    limit: number = 50,
    offset: number = 0
  ): Promise<MoneyRequestList> {
    try {
      const params = new URLSearchParams()
      if (status) params.append('status', status)
      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      const response = await apiClient.get(`/money-requests/received?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get money request statistics
   */
  static async getRequestStatistics(days: number = 30): Promise<MoneyRequestStatistics> {
    try {
      const response = await apiClient.get(`/money-requests/statistics?days=${days}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Validate money request creation
   */
  static async validateRequestCreation(
    recipientId: string,
    amount: string
  ): Promise<RequestValidationResult> {
    try {
      const response = await apiClient.post('/money-requests/validate', {
        recipient_id: recipientId,
        amount: amount
      })
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get expiring requests
   */
  static async getExpiringRequests(hours: number = 24): Promise<ExpiringRequestsResult> {
    try {
      const response = await apiClient.get(`/money-requests/expiring?hours=${hours}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Format currency amount for display
   */
  static formatCurrency(amount: string, currency: string = 'GBP'): string {
    const numAmount = parseFloat(amount)
    
    if (currency === 'GBP') {
      return new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: 'GBP',
      }).format(numAmount)
    }
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(numAmount)
  }

  /**
   * Get request status color for UI
   */
  static getRequestStatusColor(status: RequestStatus): 'success' | 'warning' | 'error' | 'info' {
    switch (status) {
      case RequestStatus.APPROVED:
        return 'success'
      case RequestStatus.DECLINED:
        return 'error'
      case RequestStatus.EXPIRED:
        return 'error'
      case RequestStatus.PENDING:
        return 'warning'
      default:
        return 'info'
    }
  }

  /**
   * Get request status display name
   */
  static getRequestStatusDisplayName(status: RequestStatus): string {
    switch (status) {
      case RequestStatus.PENDING:
        return 'Pending'
      case RequestStatus.APPROVED:
        return 'Approved'
      case RequestStatus.DECLINED:
        return 'Declined'
      case RequestStatus.EXPIRED:
        return 'Expired'
      default:
        return 'Unknown'
    }
  }

  /**
   * Check if request is expired
   */
  static isRequestExpired(request: MoneyRequest): boolean {
    if (!request.expires_at) return false
    return new Date(request.expires_at) < new Date()
  }

  /**
   * Check if request is expiring soon
   */
  static isRequestExpiringSoon(request: MoneyRequest, hoursThreshold: number = 24): boolean {
    if (!request.expires_at || request.status !== RequestStatus.PENDING) return false
    
    const expiryTime = new Date(request.expires_at).getTime()
    const now = new Date().getTime()
    const hoursUntilExpiry = (expiryTime - now) / (1000 * 60 * 60)
    
    return hoursUntilExpiry <= hoursThreshold && hoursUntilExpiry > 0
  }

  /**
   * Get time until expiry
   */
  static getTimeUntilExpiry(request: MoneyRequest): {
    expired: boolean
    days: number
    hours: number
    minutes: number
  } {
    if (!request.expires_at) {
      return { expired: false, days: 0, hours: 0, minutes: 0 }
    }

    const expiryTime = new Date(request.expires_at).getTime()
    const now = new Date().getTime()
    const timeDiff = expiryTime - now

    if (timeDiff <= 0) {
      return { expired: true, days: 0, hours: 0, minutes: 0 }
    }

    const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24))
    const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60))

    return { expired: false, days, hours, minutes }
  }

  /**
   * Format time until expiry for display
   */
  static formatTimeUntilExpiry(request: MoneyRequest): string {
    const timeInfo = this.getTimeUntilExpiry(request)
    
    if (timeInfo.expired) {
      return 'Expired'
    }

    if (timeInfo.days > 0) {
      return `${timeInfo.days} day${timeInfo.days > 1 ? 's' : ''} remaining`
    }

    if (timeInfo.hours > 0) {
      return `${timeInfo.hours} hour${timeInfo.hours > 1 ? 's' : ''} remaining`
    }

    if (timeInfo.minutes > 0) {
      return `${timeInfo.minutes} minute${timeInfo.minutes > 1 ? 's' : ''} remaining`
    }

    return 'Expiring soon'
  }

  /**
   * Validate request amount
   */
  static validateAmount(amount: string): { valid: boolean; error?: string } {
    if (!amount || amount.trim() === '') {
      return { valid: false, error: 'Amount is required' }
    }

    const numAmount = parseFloat(amount)
    
    if (isNaN(numAmount)) {
      return { valid: false, error: 'Amount must be a valid number' }
    }

    if (numAmount <= 0) {
      return { valid: false, error: 'Amount must be positive' }
    }

    if (numAmount > 10000) {
      return { valid: false, error: 'Amount cannot exceed £10,000' }
    }

    // Check for reasonable decimal places
    const decimalPlaces = (amount.split('.')[1] || '').length
    if (decimalPlaces > 2) {
      return { valid: false, error: 'Amount cannot have more than 2 decimal places' }
    }

    return { valid: true }
  }

  /**
   * Validate request note
   */
  static validateNote(note?: string): { valid: boolean; error?: string } {
    if (!note) {
      return { valid: true } // Note is optional
    }

    if (note.length > 500) {
      return { valid: false, error: 'Note cannot exceed 500 characters' }
    }

    return { valid: true }
  }

  /**
   * Validate expiry days
   */
  static validateExpiryDays(days?: number): { valid: boolean; error?: string } {
    if (days === undefined || days === null) {
      return { valid: true } // Optional, will use default
    }

    if (!Number.isInteger(days) || days < 1 || days > 30) {
      return { valid: false, error: 'Expiry days must be between 1 and 30' }
    }

    return { valid: true }
  }

  /**
   * Group requests by status
   */
  static groupRequestsByStatus(requests: MoneyRequest[]): Record<RequestStatus, MoneyRequest[]> {
    const grouped: Record<RequestStatus, MoneyRequest[]> = {
      [RequestStatus.PENDING]: [],
      [RequestStatus.APPROVED]: [],
      [RequestStatus.DECLINED]: [],
      [RequestStatus.EXPIRED]: [],
    }
    
    requests.forEach(request => {
      grouped[request.status].push(request)
    })
    
    return grouped
  }

  /**
   * Sort requests by various criteria
   */
  static sortRequests(
    requests: MoneyRequest[], 
    sortBy: 'date' | 'amount' | 'status' | 'expiry',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): MoneyRequest[] {
    const sorted = [...requests].sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'date':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          break
        case 'amount':
          comparison = parseFloat(a.amount) - parseFloat(b.amount)
          break
        case 'status':
          comparison = a.status.localeCompare(b.status)
          break
        case 'expiry':
          const aExpiry = a.expires_at ? new Date(a.expires_at).getTime() : 0
          const bExpiry = b.expires_at ? new Date(b.expires_at).getTime() : 0
          comparison = aExpiry - bExpiry
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return sorted
  }

  /**
   * Filter requests by text search
   */
  static searchRequests(requests: MoneyRequest[], searchText: string): MoneyRequest[] {
    if (!searchText.trim()) {
      return requests
    }

    const searchLower = searchText.toLowerCase()
    
    return requests.filter(request => {
      return (
        request.note?.toLowerCase().includes(searchLower) ||
        request.requester_name?.toLowerCase().includes(searchLower) ||
        request.recipient_name?.toLowerCase().includes(searchLower) ||
        request.amount.includes(searchText) ||
        request.status.toLowerCase().includes(searchLower)
      )
    })
  }

  /**
   * Get request summary for display
   */
  static getRequestSummary(requests: MoneyRequest[], currentUserId: string): {
    totalSent: number
    totalReceived: number
    pendingSent: number
    pendingReceived: number
    approvedSent: number
    approvedReceived: number
  } {
    let totalSent = 0
    let totalReceived = 0
    let pendingSent = 0
    let pendingReceived = 0
    let approvedSent = 0
    let approvedReceived = 0

    requests.forEach(request => {
      const amount = parseFloat(request.amount)
      
      if (request.requester_id === currentUserId) {
        // Sent request
        totalSent += amount
        if (request.status === RequestStatus.PENDING) {
          pendingSent += amount
        } else if (request.status === RequestStatus.APPROVED) {
          approvedSent += amount
        }
      } else {
        // Received request
        totalReceived += amount
        if (request.status === RequestStatus.PENDING) {
          pendingReceived += amount
        } else if (request.status === RequestStatus.APPROVED) {
          approvedReceived += amount
        }
      }
    })

    return {
      totalSent,
      totalReceived,
      pendingSent,
      pendingReceived,
      approvedSent,
      approvedReceived,
    }
  }

  /**
   * Check if user can respond to request
   */
  static canRespondToRequest(request: MoneyRequest, currentUserId: string): boolean {
    return (
      request.recipient_id === currentUserId &&
      request.status === RequestStatus.PENDING &&
      !this.isRequestExpired(request)
    )
  }

  /**
   * Check if user can cancel request
   */
  static canCancelRequest(request: MoneyRequest, currentUserId: string): boolean {
    return (
      request.requester_id === currentUserId &&
      request.status === RequestStatus.PENDING
    )
  }
}

export const moneyRequestsService = MoneyRequestsService
export default MoneyRequestsService