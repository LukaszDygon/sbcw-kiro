/**
 * Audit service for SoftBankCashWire frontend
 */
import apiClient, { handleApiError } from './api'

export interface AuditLog {
  id: string
  user_id?: string
  user_name?: string
  action_type: string
  entity_type: string
  entity_id?: string
  old_values?: Record<string, any>
  new_values?: Record<string, any>
  ip_address?: string
  user_agent?: string
  created_at: string
  is_system_event: boolean
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  changes?: Record<string, { old: any; new: any }>
}

export interface AuditLogFilters {
  user_id?: string
  action_type?: string
  entity_type?: string
  start_date?: string
  end_date?: string
  ip_address?: string
  severity?: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  page?: number
  per_page?: number
  include_system_events?: boolean
}

export interface AuditLogList {
  audit_logs: AuditLog[]
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

export interface AuditReport {
  report_type: string
  period: {
    start_date: string
    end_date: string
    duration_days: number
  }
  generated_at: string
  generated_by: string
  user_activity?: {
    total_users_active: number
    total_user_actions: number
    user_details: Record<string, {
      user_name: string
      user_email: string
      total_actions: number
      action_types: Record<string, number>
      login_count: number
      transaction_count: number
      last_activity?: string
    }>
  }
  transactions?: {
    total_transaction_events: number
    transaction_types: Record<string, number>
    failed_transactions: number
    bulk_transfers: number
    total_amount_processed: number
  }
  security?: {
    total_security_events: number
    failed_logins: number
    successful_logins: number
    security_alerts: number
    unique_ip_addresses: number
    suspicious_activities: Array<{
      timestamp: string
      action_type: string
      user_id?: string
      ip_address?: string
      details?: Record<string, any>
    }>
  }
  system?: {
    total_system_events: number
    system_errors: number
    system_warnings: number
    system_info: number
    event_types: Record<string, number>
  }
  compliance?: {
    total_audit_entries: number
    data_integrity_checks: {
      entries_with_timestamps: number
      entries_with_user_context: number
      entries_with_ip_tracking: number
    }
    retention_compliance: {
      oldest_entry?: string
      newest_entry?: string
      retention_period_days?: number
    }
    audit_coverage: {
      user_actions_logged: number
      system_events_logged: number
      transaction_events_logged: number
    }
  }
}

export interface AuditStatistics {
  period_days: number
  total_entries: number
  user_actions: number
  system_events: number
  action_type_breakdown: Record<string, number>
  entity_type_breakdown: Record<string, number>
  user_activity: Record<string, {
    user_name: string
    action_count: number
  }>
  daily_activity: Record<string, number>
  security_events: number
  transaction_events: number
}

export interface IntegrityCheckResult {
  total_logs_checked: number
  integrity_issues: Array<{
    log_id: string
    issue: string
    severity: 'LOW' | 'MEDIUM' | 'HIGH'
  }>
  missing_timestamps: number
  missing_action_types: number
  orphaned_user_references: number
  data_consistency_issues: number
  overall_status: 'HEALTHY' | 'WARNING' | 'CRITICAL'
}

export interface CleanupResult {
  success: boolean
  deleted_count: number
  cutoff_date?: string
  message: string
  error?: string
}

export interface ActionTypes {
  action_types: {
    USER_ACTIONS: string[]
    TRANSACTION_ACTIONS: string[]
    ACCOUNT_ACTIONS: string[]
    EVENT_ACTIONS: string[]
    MONEY_REQUEST_ACTIONS: string[]
    SYSTEM_ACTIONS: string[]
  }
  total_categories: number
  total_action_types: number
}

export interface ExportRequest {
  start_date: string
  end_date: string
  format: 'CSV' | 'JSON'
  filters?: Record<string, any>
}

export interface ExportResult {
  format: 'CSV' | 'JSON'
  data: any[]
  headers?: string[]
  metadata: {
    export_timestamp: string
    record_count: number
    date_range: {
      start: string
      end: string
    }
  }
}

class AuditService {
  /**
   * Get audit logs with filtering and pagination
   */
  static async getAuditLogs(filters?: AuditLogFilters): Promise<AuditLogList> {
    try {
      const params = new URLSearchParams()
      
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(key, value.toString())
          }
        })
      }

      const response = await apiClient.get(`/audit/logs?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Generate comprehensive audit report
   */
  static async generateAuditReport(
    startDate: string,
    endDate: string,
    reportType: 'COMPREHENSIVE' | 'TRANSACTIONS' | 'SECURITY' | 'USER_ACTIVITY' = 'COMPREHENSIVE'
  ): Promise<AuditReport> {
    try {
      const response = await apiClient.post('/audit/reports/generate', {
        start_date: startDate,
        end_date: endDate,
        report_type: reportType
      })
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get audit statistics
   */
  static async getAuditStatistics(days: number = 30): Promise<AuditStatistics> {
    try {
      const response = await apiClient.get(`/audit/statistics?days=${days}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Verify audit log integrity
   */
  static async verifyAuditIntegrity(): Promise<IntegrityCheckResult> {
    try {
      const response = await apiClient.post('/audit/integrity/verify')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Clean up old audit logs
   */
  static async cleanupOldLogs(retentionDays: number = 2555): Promise<CleanupResult> {
    try {
      const response = await apiClient.post('/audit/cleanup', {
        retention_days: retentionDays
      })
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get available action types
   */
  static async getActionTypes(): Promise<ActionTypes> {
    try {
      const response = await apiClient.get('/audit/action-types')
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Export audit logs
   */
  static async exportAuditLogs(exportRequest: ExportRequest): Promise<ExportResult> {
    try {
      const response = await apiClient.post('/audit/export', exportRequest)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get severity color for UI
   */
  static getSeverityColor(severity: string): 'success' | 'warning' | 'error' | 'info' {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
      case 'ERROR':
        return 'error'
      case 'WARNING':
        return 'warning'
      case 'INFO':
        return 'info'
      default:
        return 'success'
    }
  }

  /**
   * Format action type for display
   */
  static formatActionType(actionType: string): string {
    return actionType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ')
  }

  /**
   * Get entity type icon
   */
  static getEntityTypeIcon(entityType: string): string {
    switch (entityType.toLowerCase()) {
      case 'user':
        return '👤'
      case 'account':
        return '💰'
      case 'transaction':
        return '💸'
      case 'eventaccount':
        return '🎉'
      case 'moneyrequest':
        return '💳'
      case 'system':
        return '⚙️'
      case 'security':
        return '🔒'
      default:
        return '📄'
    }
  }

  /**
   * Check if audit log is a security event
   */
  static isSecurityEvent(auditLog: AuditLog): boolean {
    return (
      auditLog.action_type.includes('SECURITY') ||
      auditLog.action_type.includes('LOGIN') ||
      auditLog.entity_type === 'Security' ||
      auditLog.severity === 'CRITICAL'
    )
  }

  /**
   * Check if audit log is a transaction event
   */
  static isTransactionEvent(auditLog: AuditLog): boolean {
    return (
      auditLog.action_type.includes('TRANSACTION') ||
      auditLog.entity_type === 'Transaction'
    )
  }

  /**
   * Format timestamp for display
   */
  static formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString()
  }

  /**
   * Get time ago string
   */
  static getTimeAgo(timestamp: string): string {
    const now = new Date()
    const time = new Date(timestamp)
    const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000)

    if (diffInSeconds < 60) {
      return 'Just now'
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60)
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600)
      return `${hours} hour${hours > 1 ? 's' : ''} ago`
    } else {
      const days = Math.floor(diffInSeconds / 86400)
      return `${days} day${days > 1 ? 's' : ''} ago`
    }
  }

  /**
   * Filter audit logs by text search
   */
  static searchAuditLogs(auditLogs: AuditLog[], searchText: string): AuditLog[] {
    if (!searchText.trim()) {
      return auditLogs
    }

    const searchLower = searchText.toLowerCase()
    
    return auditLogs.filter(log => {
      return (
        log.action_type.toLowerCase().includes(searchLower) ||
        log.entity_type.toLowerCase().includes(searchLower) ||
        log.user_name?.toLowerCase().includes(searchLower) ||
        log.ip_address?.includes(searchText) ||
        log.entity_id?.includes(searchText) ||
        JSON.stringify(log.new_values || {}).toLowerCase().includes(searchLower)
      )
    })
  }

  /**
   * Sort audit logs by various criteria
   */
  static sortAuditLogs(
    auditLogs: AuditLog[], 
    sortBy: 'timestamp' | 'user' | 'action' | 'severity',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): AuditLog[] {
    const sorted = [...auditLogs].sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'timestamp':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          break
        case 'user':
          comparison = (a.user_name || '').localeCompare(b.user_name || '')
          break
        case 'action':
          comparison = a.action_type.localeCompare(b.action_type)
          break
        case 'severity':
          const severityOrder = { 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4 }
          comparison = (severityOrder[a.severity] || 0) - (severityOrder[b.severity] || 0)
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return sorted
  }

  /**
   * Group audit logs by date
   */
  static groupAuditLogsByDate(auditLogs: AuditLog[]): Record<string, AuditLog[]> {
    const grouped: Record<string, AuditLog[]> = {}
    
    auditLogs.forEach(log => {
      const date = new Date(log.created_at).toDateString()
      if (!grouped[date]) {
        grouped[date] = []
      }
      grouped[date].push(log)
    })
    
    return grouped
  }

  /**
   * Get audit log summary
   */
  static getAuditLogSummary(auditLogs: AuditLog[]): {
    totalLogs: number
    userActions: number
    systemEvents: number
    securityEvents: number
    transactionEvents: number
    criticalEvents: number
    uniqueUsers: number
  } {
    const uniqueUsers = new Set<string>()
    let userActions = 0
    let systemEvents = 0
    let securityEvents = 0
    let transactionEvents = 0
    let criticalEvents = 0

    auditLogs.forEach(log => {
      if (log.user_id) {
        uniqueUsers.add(log.user_id)
        userActions++
      } else {
        systemEvents++
      }

      if (this.isSecurityEvent(log)) {
        securityEvents++
      }

      if (this.isTransactionEvent(log)) {
        transactionEvents++
      }

      if (log.severity === 'CRITICAL') {
        criticalEvents++
      }
    })

    return {
      totalLogs: auditLogs.length,
      userActions,
      systemEvents,
      securityEvents,
      transactionEvents,
      criticalEvents,
      uniqueUsers: uniqueUsers.size
    }
  }

  /**
   * Validate date range for reports
   */
  static validateDateRange(startDate: string, endDate: string): { valid: boolean; error?: string } {
    try {
      const start = new Date(startDate)
      const end = new Date(endDate)

      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        return { valid: false, error: 'Invalid date format' }
      }

      if (start >= end) {
        return { valid: false, error: 'Start date must be before end date' }
      }

      const daysDiff = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
      if (daysDiff > 365) {
        return { valid: false, error: 'Date range cannot exceed 365 days' }
      }

      return { valid: true }
    } catch {
      return { valid: false, error: 'Invalid date format' }
    }
  }

  /**
   * Convert audit logs to CSV format
   */
  static convertToCSV(auditLogs: AuditLog[]): string {
    if (auditLogs.length === 0) {
      return ''
    }

    const headers = [
      'Timestamp',
      'User ID',
      'User Name',
      'Action Type',
      'Entity Type',
      'Entity ID',
      'IP Address',
      'Severity',
      'Is System Event'
    ]

    const csvRows = [
      headers.join(','),
      ...auditLogs.map(log => [
        `"${log.created_at}"`,
        `"${log.user_id || ''}"`,
        `"${log.user_name || ''}"`,
        `"${log.action_type}"`,
        `"${log.entity_type}"`,
        `"${log.entity_id || ''}"`,
        `"${log.ip_address || ''}"`,
        `"${log.severity}"`,
        `"${log.is_system_event}"`
      ].join(','))
    ]

    return csvRows.join('\n')
  }

  /**
   * Download data as file
   */
  static downloadAsFile(data: string, filename: string, mimeType: string = 'text/plain'): void {
    const blob = new Blob([data], { type: mimeType })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }
}

export default AuditService