/**
 * Account management service for SoftBankCashWire frontend
 */
import apiClient, { handleApiError } from './api'

export interface AccountBalance {
  balance: string
  available_balance: string
  currency: string
  limits: {
    minimum_balance: string
    maximum_balance: string
    overdraft_limit: string
  }
}

export interface AccountSummary {
  account_id: string
  user_id: string
  current_balance: string
  available_balance: string
  currency: string
  account_limits: {
    minimum_balance: string
    maximum_balance: string
    overdraft_limit: string
  }
  recent_activity: {
    period_days: number
    total_sent: string
    total_received: string
    net_change: string
    transaction_count: number
    transfer_count: number
    event_contribution_count: number
  }
  warnings: Array<{
    code: string
    message: string
  }>
  created_at: string
  updated_at: string
}

export interface TransactionHistoryItem {
  id: string
  sender_id: string
  recipient_id?: string
  event_id?: string
  amount: string
  transaction_type: string
  category?: string
  note?: string
  status: string
  created_at: string
  processed_at?: string
  direction: 'incoming' | 'outgoing'
  other_party_id: string
  other_party_name: string
  sender_name?: string
  recipient_name?: string
  event_name?: string
}

export interface TransactionHistory {
  transactions: TransactionHistoryItem[]
  pagination: {
    page: number
    per_page: number
    total: number
    pages: number
    has_prev: boolean
    has_next: boolean
    prev_num?: number
    next_num?: number
  }
}

export interface SpendingCategory {
  category: string
  total_amount: string
  transaction_count: number
  average_amount: string
  transactions: Array<{
    id: string
    amount: string
    recipient_name: string
    note?: string
    created_at: string
  }>
}

export interface SpendingAnalytics {
  period_days: number
  start_date: string
  end_date: string
  total_spent: string
  total_transactions: number
  average_transaction: string
  categories: SpendingCategory[]
}

export interface ValidationResult {
  valid: boolean
  current_balance: string
  new_balance: string
  amount: string
  warnings: Array<{
    code: string
    message: string
  }>
  errors: Array<{
    code: string
    message: string
  }>
}

export interface AccountStatus {
  account_status: string
  user_status: string
  balance_status: string
  issues: string[]
  recommendations: string[]
}

export interface AccountLimits {
  limits: {
    minimum_balance: string
    maximum_balance: string
    overdraft_limit: string
    overdraft_warning_threshold: string
  }
  currency: string
  description: {
    minimum_balance: string
    maximum_balance: string
    overdraft_limit: string
    overdraft_warning_threshold: string
  }
}

export interface TransactionHistoryFilters {
  start_date?: string
  end_date?: string
  transaction_type?: string
  category?: string
  min_amount?: string
  max_amount?: string
  page?: number
  per_page?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

class AccountsService {
  /**
   * Get current account balance
   */
  static async getBalance(): Promise<AccountBalance> {
    try {
      const response = await apiClient.get('/accounts/balance')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get comprehensive account summary
   */
  static async getAccountSummary(): Promise<AccountSummary> {
    try {
      const response = await apiClient.get('/accounts/summary')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get transaction history with optional filters
   */
  static async getTransactionHistory(filters?: TransactionHistoryFilters): Promise<TransactionHistory> {
    try {
      const params = new URLSearchParams()
      
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(key, value.toString())
          }
        })
      }

      const response = await apiClient.get(`/accounts/history?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get spending analytics
   */
  static async getSpendingAnalytics(periodDays: number = 30): Promise<SpendingAnalytics> {
    try {
      const response = await apiClient.get(`/accounts/analytics?period_days=${periodDays}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Validate transaction amount
   */
  static async validateTransactionAmount(amount: string): Promise<ValidationResult> {
    try {
      const response = await apiClient.post('/accounts/validate-amount', {
        amount: amount
      })
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get account status and health
   */
  static async getAccountStatus(): Promise<AccountStatus> {
    try {
      const response = await apiClient.get('/accounts/status')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get account limits and thresholds
   */
  static async getAccountLimits(): Promise<AccountLimits> {
    try {
      const response = await apiClient.get('/accounts/limits')
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
   * Check if balance is low
   */
  static isBalanceLow(balance: string, threshold: string = '50.00'): boolean {
    return parseFloat(balance) <= parseFloat(threshold)
  }

  /**
   * Check if account is in overdraft
   */
  static isInOverdraft(balance: string): boolean {
    return parseFloat(balance) < 0
  }

  /**
   * Calculate available spending amount
   */
  static getAvailableSpending(balance: string, overdraftLimit: string): string {
    const currentBalance = parseFloat(balance)
    const limit = parseFloat(overdraftLimit)
    return (currentBalance + limit).toFixed(2)
  }

  /**
   * Get balance status color for UI
   */
  static getBalanceStatusColor(balance: string): 'success' | 'warning' | 'error' {
    const amount = parseFloat(balance)
    
    if (amount < 0) {
      return 'error' // Overdraft
    } else if (amount <= 50) {
      return 'warning' // Low balance
    } else {
      return 'success' // Normal
    }
  }

  /**
   * Get transaction direction icon
   */
  static getTransactionIcon(direction: 'incoming' | 'outgoing'): string {
    return direction === 'incoming' ? '↓' : '↑'
  }

  /**
   * Get transaction amount color
   */
  static getTransactionAmountColor(direction: 'incoming' | 'outgoing'): 'success' | 'error' {
    return direction === 'incoming' ? 'success' : 'error'
  }

  /**
   * Format transaction amount with direction
   */
  static formatTransactionAmount(amount: string, direction: 'incoming' | 'outgoing', currency: string = 'GBP'): string {
    const formattedAmount = this.formatCurrency(amount, currency)
    return direction === 'incoming' ? `+${formattedAmount}` : `-${formattedAmount}`
  }

  /**
   * Group transactions by date
   */
  static groupTransactionsByDate(transactions: TransactionHistoryItem[]): Record<string, TransactionHistoryItem[]> {
    const grouped: Record<string, TransactionHistoryItem[]> = {}
    
    transactions.forEach(transaction => {
      const date = new Date(transaction.created_at).toDateString()
      if (!grouped[date]) {
        grouped[date] = []
      }
      grouped[date].push(transaction)
    })
    
    return grouped
  }

  /**
   * Calculate spending trend
   */
  static calculateSpendingTrend(analytics: SpendingAnalytics, previousAnalytics?: SpendingAnalytics): {
    trend: 'up' | 'down' | 'stable'
    percentage: number
  } {
    if (!previousAnalytics) {
      return { trend: 'stable', percentage: 0 }
    }

    const currentSpent = parseFloat(analytics.total_spent)
    const previousSpent = parseFloat(previousAnalytics.total_spent)
    
    if (previousSpent === 0) {
      return { trend: currentSpent > 0 ? 'up' : 'stable', percentage: 0 }
    }

    const percentage = ((currentSpent - previousSpent) / previousSpent) * 100
    
    if (Math.abs(percentage) < 5) {
      return { trend: 'stable', percentage: Math.round(percentage) }
    }
    
    return {
      trend: percentage > 0 ? 'up' : 'down',
      percentage: Math.round(Math.abs(percentage))
    }
  }
}

export const accountsService = AccountsService
export default AccountsService