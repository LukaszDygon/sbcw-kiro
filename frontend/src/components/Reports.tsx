/**
 * Reports component for finance team reporting and analytics
 */
import React, { useState, useEffect } from 'react'
import { financeService, AuditLog, ReportData } from '../services/finance'
import LoadingSpinner from './shared/LoadingSpinner'

interface ReportsProps {
  currentUser: {
    id: string
    role: string
  }
}

export const Reports: React.FC<ReportsProps> = () => {
  const [activeTab, setActiveTab] = useState<'reports' | 'audit' | 'export'>('reports')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Reports state
  const [reportType, setReportType] = useState<'transaction-summary' | 'user-activity' | 'event-accounts' | 'personal-analytics'>('transaction-summary')
  const [reportData, setReportData] = useState<any>(null)
  const [reportFilters, setReportFilters] = useState({
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    user_id: '',
    export_format: 'json' as 'json' | 'csv'
  })

  // Audit state
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [auditFilters, setAuditFilters] = useState({
    user_id: '',
    action_type: '',
    entity_type: '',
    start_date: '',
    end_date: '',
    severity: '',
    page: 1,
    per_page: 50
  })
  const [auditPagination, setAuditPagination] = useState({
    page: 1,
    per_page: 50,
    total: 0,
    pages: 0
  })

  // Export state
  const [exportFilters, setExportFilters] = useState({
    start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    format: 'JSON' as 'JSON' | 'CSV',
    user_id: '',
    action_type: ''
  })

  // Load audit logs when audit tab is active
  useEffect(() => {
    if (activeTab === 'audit') {
      loadAuditLogs()
    }
  }, [activeTab, auditFilters])

  const loadAuditLogs = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await financeService.getAuditLogs({
        ...auditFilters,
        start_date: auditFilters.start_date || undefined,
        end_date: auditFilters.end_date || undefined
      })

      setAuditLogs(response.audit_logs)
      setAuditPagination(response.pagination)
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load audit logs')
    } finally {
      setLoading(false)
    }
  }

  const generateReport = async () => {
    try {
      setLoading(true)
      setError(null)
      setReportData(null)

      let response: ReportData

      switch (reportType) {
        case 'transaction-summary':
          response = await financeService.generateTransactionSummary(
            reportFilters.start_date,
            reportFilters.end_date,
            reportFilters.user_id || undefined,
            reportFilters.export_format
          )
          break
        case 'user-activity':
          response = await financeService.generateUserActivityReport(
            reportFilters.start_date,
            reportFilters.end_date,
            reportFilters.export_format
          )
          break
        case 'event-accounts':
          response = await financeService.generateEventAccountReport(
            reportFilters.start_date,
            reportFilters.end_date,
            reportFilters.export_format
          )
          break
        case 'personal-analytics':
          response = await financeService.generatePersonalAnalytics(
            reportFilters.start_date,
            reportFilters.end_date,
            reportFilters.user_id || undefined,
            reportFilters.export_format
          )
          break
        default:
          throw new Error('Invalid report type')
      }

      if (response.success) {
        setReportData(response.data)
        setSuccess('Report generated successfully')
      } else {
        setError(response.error || 'Failed to generate report')
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  const exportAuditLogs = async () => {
    try {
      setLoading(true)
      setError(null)

      const exportData = await financeService.exportAuditLogs(
        exportFilters.start_date,
        exportFilters.end_date,
        exportFilters.format,
        {
          user_id: exportFilters.user_id || undefined,
          action_type: exportFilters.action_type || undefined
        }
      )

      // Create and download file
      const blob = new Blob(
        [exportFilters.format === 'JSON' ? JSON.stringify(exportData.data, null, 2) : convertToCSV(exportData.data, exportData.headers)],
        { type: exportFilters.format === 'JSON' ? 'application/json' : 'text/csv' }
      )
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = `audit_logs_${exportFilters.start_date}_${exportFilters.end_date}.${exportFilters.format.toLowerCase()}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      setSuccess(`Exported ${exportData.metadata.record_count} audit logs`)
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to export audit logs')
    } finally {
      setLoading(false)
    }
  }

  const convertToCSV = (data: any[], headers?: string[]): string => {
    if (!data.length) return ''
    
    const csvHeaders = headers || Object.keys(data[0])
    const csvRows = data.map(row => 
      csvHeaders.map(header => {
        const value = row[header]
        return typeof value === 'string' && value.includes(',') ? `"${value}"` : value
      }).join(',')
    )
    
    return [csvHeaders.join(','), ...csvRows].join('\n')
  }

  const clearMessages = () => {
    setError(null)
    setSuccess(null)
  }

  const renderReports = () => (
    <div className="space-y-6">
      {/* Report Configuration */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Generate Report</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Report Type</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="transaction-summary">Transaction Summary</option>
              <option value="user-activity">User Activity</option>
              <option value="event-accounts">Event Accounts</option>
              <option value="personal-analytics">Personal Analytics</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={reportFilters.start_date}
              onChange={(e) => setReportFilters(prev => ({ ...prev, start_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={reportFilters.end_date}
              onChange={(e) => setReportFilters(prev => ({ ...prev, end_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
            <select
              value={reportFilters.export_format}
              onChange={(e) => setReportFilters(prev => ({ ...prev, export_format: e.target.value as 'json' | 'csv' }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
            </select>
          </div>
        </div>

        {(reportType === 'transaction-summary' || reportType === 'personal-analytics') && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">User ID (Optional)</label>
            <input
              type="text"
              value={reportFilters.user_id}
              onChange={(e) => setReportFilters(prev => ({ ...prev, user_id: e.target.value }))}
              placeholder="Leave empty for all users"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        <button
          onClick={generateReport}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Generating...' : 'Generate Report'}
        </button>
      </div>

      {/* Report Results */}
      {reportData && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Report Results</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap overflow-x-auto">
              {JSON.stringify(reportData, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )

  const renderAuditLogs = () => (
    <div className="space-y-6">
      {/* Audit Filters */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Filter Audit Logs</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">User ID</label>
            <input
              type="text"
              value={auditFilters.user_id}
              onChange={(e) => setAuditFilters(prev => ({ ...prev, user_id: e.target.value }))}
              placeholder="Filter by user ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Action Type</label>
            <input
              type="text"
              value={auditFilters.action_type}
              onChange={(e) => setAuditFilters(prev => ({ ...prev, action_type: e.target.value }))}
              placeholder="Filter by action"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Entity Type</label>
            <input
              type="text"
              value={auditFilters.entity_type}
              onChange={(e) => setAuditFilters(prev => ({ ...prev, entity_type: e.target.value }))}
              placeholder="Filter by entity"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={auditFilters.start_date}
              onChange={(e) => setAuditFilters(prev => ({ ...prev, start_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={auditFilters.end_date}
              onChange={(e) => setAuditFilters(prev => ({ ...prev, end_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Severity</label>
          <select
            value={auditFilters.severity}
            onChange={(e) => setAuditFilters(prev => ({ ...prev, severity: e.target.value }))}
            className="w-full md:w-48 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Severities</option>
            <option value="INFO">Info</option>
            <option value="WARNING">Warning</option>
            <option value="ERROR">Error</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Audit Logs ({auditPagination.total})</h3>
        </div>
        
        {loading ? (
          <div className="p-6 text-center">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.user_name || log.user_id || 'System'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.action_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.entity_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        log.severity === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                        log.severity === 'ERROR' ? 'bg-orange-100 text-orange-800' :
                        log.severity === 'WARNING' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {log.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.ip_address || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {auditPagination.pages > 1 && (
          <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing page {auditPagination.page} of {auditPagination.pages}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setAuditFilters(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={auditPagination.page === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setAuditFilters(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={auditPagination.page === auditPagination.pages}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )

  const renderExport = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Export Data</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              type="date"
              value={exportFilters.start_date}
              onChange={(e) => setExportFilters(prev => ({ ...prev, start_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              type="date"
              value={exportFilters.end_date}
              onChange={(e) => setExportFilters(prev => ({ ...prev, end_date: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
            <select
              value={exportFilters.format}
              onChange={(e) => setExportFilters(prev => ({ ...prev, format: e.target.value as 'JSON' | 'CSV' }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="JSON">JSON</option>
              <option value="CSV">CSV</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">User ID (Optional)</label>
            <input
              type="text"
              value={exportFilters.user_id}
              onChange={(e) => setExportFilters(prev => ({ ...prev, user_id: e.target.value }))}
              placeholder="Filter by specific user"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Action Type (Optional)</label>
            <input
              type="text"
              value={exportFilters.action_type}
              onChange={(e) => setExportFilters(prev => ({ ...prev, action_type: e.target.value }))}
              placeholder="Filter by action type"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button
          onClick={exportAuditLogs}
          disabled={loading}
          className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
        >
          {loading ? 'Exporting...' : 'Export Audit Logs'}
        </button>
      </div>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Finance Reports</h1>
        <p className="mt-2 text-gray-600">Generate reports and view audit trails</p>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
            <div className="ml-auto pl-3">
              <button onClick={clearMessages} className="text-red-400 hover:text-red-600">
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-800">{success}</p>
            </div>
            <div className="ml-auto pl-3">
              <button onClick={clearMessages} className="text-green-400 hover:text-green-600">
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('reports')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'reports'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Generate Reports
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'audit'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Audit Trail
          </button>
          <button
            onClick={() => setActiveTab('export')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'export'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Export Data
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'reports' && renderReports()}
      {activeTab === 'audit' && renderAuditLogs()}
      {activeTab === 'export' && renderExport()}
    </div>
  )
}

export default Reports