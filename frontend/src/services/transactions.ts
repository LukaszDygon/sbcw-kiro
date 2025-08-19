/**
 * Transaction service for SoftBankCashWire frontend
 */
import apiClient, { handleApiError } from './api'
import { Transaction, TransactionType } from '../types'

export interface SendMoneyRequest {
  recipient_id: string
  amount: string
  category?: string
  note?: string
}

export interface BulkRecipient {
  recipient_id: string
  amount: string
  category?: string
  note?: string
}

export interface SendBulkMoneyRequest {
  recipients: BulkRecipient[]
}

export interface TransactionValidationRequest {
  recipient_id?: string
  amount: string
  transaction_type?: TransactionType
}

export interface TransactionValidationResult {
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

export interface SendMoneyResult {
  success: boolean
  transaction: Transaction
  sender_balance: string
  recipient_balance: string
  warnings: Array<{
    code: string
    message: string
  }>
}

export interface BulkTransactionResult {
  transaction: Transaction
  recipient_balance: string
}

export interface SendBulkMoneyResult {
  success: boolean
  total_amount: string
  recipient_count: number
  sender_balance: string
  transactions: BulkTransactionResult[]
  warnings: Array<{
    code: string
    message: string
  }>
}

export interface TransactionStatistics {
  period_days: number
  total_transactions: number
  total_sent: string
  total_received: string
  net_amount: string
  sent_count: number
  received_count: number
  average_sent: string
  average_received: string
  top_partners: Array<{
    user_id: string
    name: string
    transaction_count: number
    total_amount: string
  }>
}

export interface TransactionCategory {
  id: string
  name: string
  description: string
}

export interface CancelTransactionResult {
  success: boolean
  message: string
  transaction: Transaction
}

class TransactionsService {
  /**
   * Send money to another user
   */
  static async sendMoney(request: SendMoneyRequest): Promise<SendMoneyResult> {
    try {
      const response = await apiClient.post('/transactions/send', request)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Send money to multiple recipients
   */
  static async sendBulkMoney(request: SendBulkMoneyRequest): Promise<SendBulkMoneyResult> {
    try {
      const response = await apiClient.post('/transactions/send-bulk', request)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Validate a transaction before processing
   */
  static async validateTransaction(request: TransactionValidationRequest): Promise<TransactionValidationResult> {
    try {
      const response = await apiClient.post('/transactions/validate', request)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get transaction details by ID
   */
  static async getTransaction(transactionId: string): Promise<{ transaction: Transaction }> {
    try {
      const response = await apiClient.get(`/transactions/${transactionId}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get recent transactions
   */
  static async getRecentTransactions(limit: number = 10): Promise<{ transactions: Transaction[]; count: number }> {
    try {
      const response = await apiClient.get(`/transactions/recent?limit=${limit}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get transaction statistics
   */
  static async getTransactionStatistics(days: number = 30): Promise<TransactionStatistics> {
    try {
      const response = await apiClient.get(`/transactions/statistics?days=${days}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Cancel a transaction
   */
  static async cancelTransaction(transactionId: string): Promise<CancelTransactionResult> {
    try {
      const response = await apiClient.post(`/transactions/${transactionId}/cancel`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get available transaction categories
   */
  static async getTransactionCategories(): Promise<{ categories: TransactionCategory[] }> {
    try {
      const response = await apiClient.get('/transactions/categories')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Format transaction amount for display
   */
  static formatTransactionAmount(amount: string, currency: string = 'GBP'): string {
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
   * Get transaction status color for UI
   */
  static getTransactionStatusColor(status: string): 'success' | 'warning' | 'error' {
    switch (status.toUpperCase()) {
      case 'COMPLETED':
        return 'success'
      case 'FAILED':
        return 'error'
      default:
        return 'warning'
    }
  }

  /**
   * Get transaction type display name
   */
  static getTransactionTypeDisplayName(type: TransactionType): string {
    switch (type) {
      case TransactionType.TRANSFER:
        return 'Transfer'
      case TransactionType.EVENT_CONTRIBUTION:
        return 'Event Contribution'
      default:
        return 'Unknown'
    }
  }

  /**
   * Get transaction direction from user perspective
   */
  static getTransactionDirection(transaction: Transaction, currentUserId: string): 'incoming' | 'outgoing' {
    return transaction.sender_id === currentUserId ? 'outgoing' : 'incoming'
  }

  /**
   * Get other party name for transaction
   */
  static getOtherPartyName(transaction: Transaction, currentUserId: string): string {
    if (transaction.sender_id === currentUserId) {
      // Outgoing transaction
      if (transaction.recipient_name) {
        return transaction.recipient_name
      }
      if (transaction.event_name) {
        return transaction.event_name
      }
      return 'Unknown'
    } else {
      // Incoming transaction
      return transaction.sender_name || 'Unknown'
    }
  }

  /**
   * Validate transaction amount format
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
   * Validate transaction note
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
   * Validate transaction category
   */
  static validateCategory(category?: string): { valid: boolean; error?: string } {
    if (!category) {
      return { valid: true } // Category is optional
    }

    if (category.length > 100) {
      return { valid: false, error: 'Category cannot exceed 100 characters' }
    }

    return { valid: true }
  }

  /**
   * Calculate total amount for bulk transfer
   */
  static calculateBulkTotal(recipients: BulkRecipient[]): string {
    const total = recipients.reduce((sum, recipient) => {
      return sum + parseFloat(recipient.amount || '0')
    }, 0)
    
    return total.toFixed(2)
  }

  /**
   * Validate bulk recipients
   */
  static validateBulkRecipients(recipients: BulkRecipient[]): { valid: boolean; errors: string[] } {
    const errors: string[] = []

    if (!recipients || recipients.length === 0) {
      errors.push('At least one recipient is required')
      return { valid: false, errors }
    }

    if (recipients.length > 50) {
      errors.push('Cannot send to more than 50 recipients at once')
      return { valid: false, errors }
    }

    recipients.forEach((recipient, index) => {
      const recipientNum = index + 1

      if (!recipient.recipient_id) {
        errors.push(`Recipient ${recipientNum}: Recipient is required`)
      }

      const amountValidation = this.validateAmount(recipient.amount)
      if (!amountValidation.valid) {
        errors.push(`Recipient ${recipientNum}: ${amountValidation.error}`)
      }

      const noteValidation = this.validateNote(recipient.note)
      if (!noteValidation.valid) {
        errors.push(`Recipient ${recipientNum}: ${noteValidation.error}`)
      }

      const categoryValidation = this.validateCategory(recipient.category)
      if (!categoryValidation.valid) {
        errors.push(`Recipient ${recipientNum}: ${categoryValidation.error}`)
      }
    })

    return { valid: errors.length === 0, errors }
  }

  /**
   * Group transactions by date
   */
  static groupTransactionsByDate(transactions: Transaction[]): Record<string, Transaction[]> {
    const grouped: Record<string, Transaction[]> = {}
    
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
   * Get transaction summary for a period
   */
  static getTransactionSummary(transactions: Transaction[], currentUserId: string): {
    totalSent: number
    totalReceived: number
    netAmount: number
    sentCount: number
    receivedCount: number
  } {
    let totalSent = 0
    let totalReceived = 0
    let sentCount = 0
    let receivedCount = 0

    transactions.forEach(transaction => {
      const amount = parseFloat(transaction.amount)
      
      if (transaction.sender_id === currentUserId) {
        totalSent += amount
        sentCount++
      } else {
        totalReceived += amount
        receivedCount++
      }
    })

    return {
      totalSent,
      totalReceived,
      netAmount: totalReceived - totalSent,
      sentCount,
      receivedCount,
    }
  }

  /**
   * Search transactions by text
   */
  static searchTransactions(transactions: Transaction[], searchText: string): Transaction[] {
    if (!searchText.trim()) {
      return transactions
    }

    const searchLower = searchText.toLowerCase()
    
    return transactions.filter(transaction => {
      return (
        transaction.note?.toLowerCase().includes(searchLower) ||
        transaction.category?.toLowerCase().includes(searchLower) ||
        transaction.sender_name?.toLowerCase().includes(searchLower) ||
        transaction.recipient_name?.toLowerCase().includes(searchLower) ||
        transaction.event_name?.toLowerCase().includes(searchLower) ||
        transaction.amount.includes(searchText)
      )
    })
  }

  /**
   * Sort transactions by various criteria
   */
  static sortTransactions(
    transactions: Transaction[], 
    sortBy: 'date' | 'amount' | 'recipient' | 'category',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Transaction[] {
    const sorted = [...transactions].sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'date':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          break
        case 'amount':
          comparison = parseFloat(a.amount) - parseFloat(b.amount)
          break
        case 'recipient':
          const aName = a.recipient_name || a.event_name || ''
          const bName = b.recipient_name || b.event_name || ''
          comparison = aName.localeCompare(bName)
          break
        case 'category':
          comparison = (a.category || '').localeCompare(b.category || '')
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return sorted
  }
}

export const transactionsService = TransactionsService
export default TransactionsService