/**
 * Finance service for reporting and audit functionality
 */
import api from './api'

export interface AuditLog {
    id: string
    user_id?: string
    user_name?: string
    action_type: string
    entity_type: string
    entity_id?: string
    old_values?: any
    new_values?: any
    ip_address?: string
    user_agent?: string
    severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
    created_at: string
}

export interface AuditLogsResponse {
    audit_logs: AuditLog[]
    pagination: {
        page: number
        per_page: number
        total: number
        pages: number
        has_next: boolean
        has_prev: boolean
    }
}

export interface AuditReport {
    report_type: string
    start_date: string
    end_date: string
    summary: {
        total_logs: number
        unique_users: number
        action_types: Record<string, number>
        severity_breakdown: Record<string, number>
    }
    details: AuditLog[]
    generated_at: string
}

export interface AuditStatistics {
    period_days: number
    total_logs: number
    unique_users: number
    action_type_breakdown: Record<string, number>
    severity_breakdown: Record<string, number>
    daily_activity: Array<{
        date: string
        log_count: number
    }>
    top_users: Array<{
        user_id: string
        user_name: string
        action_count: number
    }>
}

export interface IntegrityResult {
    overall_status: 'HEALTHY' | 'WARNING' | 'CRITICAL'
    total_logs_checked: number
    integrity_issues: Array<{
        log_id: string
        issue_type: string
        description: string
    }>
    last_check: string
}

export interface ExportData {
    format: 'JSON' | 'CSV'
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

export interface ReportData {
    success: boolean
    data?: any
    error?: string
}

export const financeService = {
    /**
     * Get audit logs with filtering and pagination
     */
    async getAuditLogs(params?: {
        user_id?: string
        action_type?: string
        entity_type?: string
        start_date?: string
        end_date?: string
        ip_address?: string
        severity?: string
        page?: number
        per_page?: number
        include_system_events?: boolean
    }): Promise<AuditLogsResponse> {
        const searchParams = new URLSearchParams()

        if (params?.user_id) searchParams.append('user_id', params.user_id)
        if (params?.action_type) searchParams.append('action_type', params.action_type)
        if (params?.entity_type) searchParams.append('entity_type', params.entity_type)
        if (params?.start_date) searchParams.append('start_date', params.start_date)
        if (params?.end_date) searchParams.append('end_date', params.end_date)
        if (params?.ip_address) searchParams.append('ip_address', params.ip_address)
        if (params?.severity) searchParams.append('severity', params.severity)
        if (params?.page) searchParams.append('page', params.page.toString())
        if (params?.per_page) searchParams.append('per_page', params.per_page.toString())
        if (params?.include_system_events !== undefined) {
            searchParams.append('include_system_events', params.include_system_events.toString())
        }

        const response = await api.get(`/audit/logs?${searchParams.toString()}`)
        return response.data
    },

    /**
     * Generate comprehensive audit report
     */
    async generateAuditReport(
        startDate: string,
        endDate: string,
        reportType: 'COMPREHENSIVE' | 'TRANSACTIONS' | 'SECURITY' | 'USER_ACTIVITY' = 'COMPREHENSIVE'
    ): Promise<AuditReport> {
        const response = await api.post('/audit/reports/generate', {
            start_date: startDate,
            end_date: endDate,
            report_type: reportType
        })
        return response.data
    },

    /**
     * Get audit statistics
     */
    async getAuditStatistics(days: number = 30): Promise<AuditStatistics> {
        const response = await api.get(`/audit/statistics?days=${days}`)
        return response.data
    },

    /**
     * Verify audit log integrity
     */
    async verifyAuditIntegrity(): Promise<IntegrityResult> {
        const response = await api.post('/audit/integrity/verify')
        return response.data
    },

    /**
     * Export audit logs
     */
    async exportAuditLogs(
        startDate: string,
        endDate: string,
        format: 'JSON' | 'CSV' = 'JSON',
        filters?: {
            user_id?: string
            action_type?: string
        }
    ): Promise<ExportData> {
        const response = await api.post('/audit/export', {
            start_date: startDate,
            end_date: endDate,
            format,
            filters
        })
        return response.data
    },

    /**
     * Get available action types
     */
    async getActionTypes(): Promise<{
        action_types: Record<string, string[]>
        total_categories: number
        total_action_types: number
    }> {
        const response = await api.get('/audit/action-types')
        return response.data
    },

    /**
     * Generate transaction summary report
     */
    async generateTransactionSummary(
        startDate: string,
        endDate: string,
        userId?: string,
        exportFormat: 'json' | 'csv' = 'json'
    ): Promise<ReportData> {
        const response = await api.post('/reporting/transaction-summary', {
            start_date: startDate,
            end_date: endDate,
            user_id: userId,
            export_format: exportFormat
        })
        return response.data
    },

    /**
     * Generate user activity report
     */
    async generateUserActivityReport(
        startDate: string,
        endDate: string,
        exportFormat: 'json' | 'csv' = 'json'
    ): Promise<ReportData> {
        const response = await api.post('/reporting/user-activity', {
            start_date: startDate,
            end_date: endDate,
            export_format: exportFormat
        })
        return response.data
    },

    /**
     * Generate event account report
     */
    async generateEventAccountReport(
        startDate: string,
        endDate: string,
        exportFormat: 'json' | 'csv' = 'json'
    ): Promise<ReportData> {
        const response = await api.post('/reporting/event-accounts', {
            start_date: startDate,
            end_date: endDate,
            export_format: exportFormat
        })
        return response.data
    },

    /**
     * Generate personal analytics
     */
    async generatePersonalAnalytics(
        startDate: string,
        endDate: string,
        userId?: string,
        exportFormat: 'json' | 'csv' = 'json'
    ): Promise<ReportData> {
        const response = await api.post('/reporting/personal-analytics', {
            start_date: startDate,
            end_date: endDate,
            user_id: userId,
            export_format: exportFormat
        })
        return response.data
    },

    /**
     * Get available reports for current user
     */
    async getAvailableReports(): Promise<{
        success: boolean
        reports: string[]
    }> {
        const response = await api.get('/reporting/available')
        return response.data
    }
}