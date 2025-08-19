/**
 * AdminPanel component for user management and system configuration
 */
import React, { useState, useEffect } from 'react'
import { adminService, User, UserDetails, SystemConfig } from '../services/admin'
import LoadingSpinner from './shared/LoadingSpinner'

interface AdminPanelProps {
  currentUser: {
    id: string
    role: string
  }
}

export const AdminPanel: React.FC<AdminPanelProps> = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState<'users' | 'config' | 'maintenance'>('users')
  const [users, setUsers] = useState<User[]>([])
  const [selectedUser, setSelectedUser] = useState<UserDetails | null>(null)
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  
  // User management state
  const [userFilters, setUserFilters] = useState({
    role: '',
    status: '',
    search: ''
  })
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0
  })

  // Load users on component mount and filter changes
  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers()
    }
  }, [activeTab, userFilters, pagination.page])

  // Load system config when config tab is active
  useEffect(() => {
    if (activeTab === 'config') {
      loadSystemConfig()
    }
  }, [activeTab])

  const loadUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await adminService.getUsers({
        ...userFilters,
        page: pagination.page,
        per_page: pagination.per_page
      })
      
      setUsers(response.users)
      setPagination(prev => ({
        ...prev,
        total: response.pagination.total,
        pages: response.pagination.pages
      }))
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const loadUserDetails = async (userId: string) => {
    try {
      setLoading(true)
      setError(null)
      
      const userDetails = await adminService.getUserDetails(userId)
      setSelectedUser(userDetails)
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load user details')
    } finally {
      setLoading(false)
    }
  }

  const loadSystemConfig = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const config = await adminService.getSystemConfig()
      setSystemConfig(config)
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to load system configuration')
    } finally {
      setLoading(false)
    }
  }

  const updateUserStatus = async (userId: string, status: string, reason: string) => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await adminService.updateUserStatus(userId, status, reason)
      setSuccess(result.message)
      
      // Refresh users list and selected user details
      await loadUsers()
      if (selectedUser?.id === userId) {
        await loadUserDetails(userId)
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to update user status')
    } finally {
      setLoading(false)
    }
  }

  const updateUserRole = async (userId: string, role: string, reason: string) => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await adminService.updateUserRole(userId, role, reason)
      setSuccess(result.message)
      
      // Refresh users list and selected user details
      await loadUsers()
      if (selectedUser?.id === userId) {
        await loadUserDetails(userId)
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to update user role')
    } finally {
      setLoading(false)
    }
  }

  const performMaintenance = async (task: string, parameters?: any) => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await adminService.performMaintenance(task, parameters)
      
      if (result.success) {
        setSuccess(result.message)
      } else {
        setError(result.message)
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to perform maintenance task')
    } finally {
      setLoading(false)
    }
  }

  const clearMessages = () => {
    setError(null)
    setSuccess(null)
  }

  const renderUserManagement = () => (
    <div className="space-y-6">
      {/* User Filters */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Filter Users</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
            <select
              value={userFilters.role}
              onChange={(e) => setUserFilters(prev => ({ ...prev, role: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Roles</option>
              <option value="EMPLOYEE">Employee</option>
              <option value="ADMIN">Admin</option>
              <option value="FINANCE">Finance</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={userFilters.status}
              onChange={(e) => setUserFilters(prev => ({ ...prev, status: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <input
              type="text"
              value={userFilters.search}
              onChange={(e) => setUserFilters(prev => ({ ...prev, search: e.target.value }))}
              placeholder="Search by name or email..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Users List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Users ({pagination.total})</h3>
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
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Balance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Login
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.role === 'ADMIN' ? 'bg-purple-100 text-purple-800' :
                        user.role === 'FINANCE' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.account_status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
                        user.account_status === 'SUSPENDED' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {user.account_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      £{user.account.balance}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => loadUserDetails(user.id)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {pagination.pages > 1 && (
          <div className="px-6 py-3 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing page {pagination.page} of {pagination.pages}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={pagination.page === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={pagination.page === pagination.pages}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* User Details Modal */}
      {selectedUser && (
        <UserDetailsModal
          user={selectedUser}
          currentUserId={currentUser.id}
          onClose={() => setSelectedUser(null)}
          onUpdateStatus={updateUserStatus}
          onUpdateRole={updateUserRole}
        />
      )}
    </div>
  )

  const renderSystemConfig = () => (
    <div className="space-y-6">
      {systemConfig && (
        <>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Application Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <p className="text-sm text-gray-900">{systemConfig.application.name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Version</label>
                <p className="text-sm text-gray-900">{systemConfig.application.version}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Environment</label>
                <p className="text-sm text-gray-900">{systemConfig.application.environment}</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(systemConfig.features).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {value ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">System Limits</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(systemConfig.limits).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  <span className="text-sm text-gray-900">{value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Security Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(systemConfig.security).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                  <span className="text-sm text-gray-900">
                    {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )

  const renderMaintenance = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-medium text-gray-900 mb-4">System Maintenance</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Clean Up Sessions</h4>
              <p className="text-sm text-gray-500">Remove expired user sessions from the database</p>
            </div>
            <button
              onClick={() => performMaintenance('cleanup_sessions')}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              Run Cleanup
            </button>
          </div>

          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Optimize Database</h4>
              <p className="text-sm text-gray-500">Optimize database performance and reclaim space</p>
            </div>
            <button
              onClick={() => performMaintenance('optimize_database')}
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              Optimize
            </button>
          </div>

          <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Verify Integrity</h4>
              <p className="text-sm text-gray-500">Verify audit log integrity and system consistency</p>
            </div>
            <button
              onClick={() => performMaintenance('verify_integrity')}
              disabled={loading}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
            >
              Verify
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
        <p className="mt-2 text-gray-600">Manage users and system configuration</p>
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
            onClick={() => setActiveTab('users')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'users'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            User Management
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'config'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            System Configuration
          </button>
          <button
            onClick={() => setActiveTab('maintenance')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'maintenance'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Maintenance
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'users' && renderUserManagement()}
      {activeTab === 'config' && renderSystemConfig()}
      {activeTab === 'maintenance' && renderMaintenance()}
    </div>
  )
}

// User Details Modal Component
interface UserDetailsModalProps {
  user: UserDetails
  currentUserId: string
  onClose: () => void
  onUpdateStatus: (userId: string, status: string, reason: string) => void
  onUpdateRole: (userId: string, role: string, reason: string) => void
}

const UserDetailsModal: React.FC<UserDetailsModalProps> = ({
  user,
  currentUserId,
  onClose,
  onUpdateStatus,
  onUpdateRole
}) => {
  const [statusForm, setStatusForm] = useState({
    status: user.account_status,
    reason: ''
  })
  const [roleForm, setRoleForm] = useState({
    role: user.role,
    reason: ''
  })

  const handleStatusUpdate = (e: React.FormEvent) => {
    e.preventDefault()
    onUpdateStatus(user.id, statusForm.status, statusForm.reason)
    setStatusForm({ status: user.account_status, reason: '' })
  }

  const handleRoleUpdate = (e: React.FormEvent) => {
    e.preventDefault()
    onUpdateRole(user.id, roleForm.role, roleForm.reason)
    setRoleForm({ role: user.role, reason: '' })
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">User Details: {user.name}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* User Information */}
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Basic Information</h4>
              <div className="space-y-2 text-sm">
                <div><strong>Email:</strong> {user.email}</div>
                <div><strong>Role:</strong> {user.role}</div>
                <div><strong>Status:</strong> {user.account_status}</div>
                <div><strong>Balance:</strong> £{user.account.balance}</div>
                <div><strong>Created:</strong> {new Date(user.created_at).toLocaleDateString()}</div>
                <div><strong>Last Login:</strong> {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</div>
              </div>
            </div>

            {/* Recent Transactions */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Recent Transactions</h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {user.recent_transactions.length > 0 ? (
                  user.recent_transactions.map((transaction) => (
                    <div key={transaction.id} className="text-sm border-b border-gray-200 pb-2">
                      <div className="flex justify-between">
                        <span>{transaction.type === 'sent' ? 'Sent to' : 'Received from'} {transaction.other_party}</span>
                        <span className={transaction.type === 'sent' ? 'text-red-600' : 'text-green-600'}>
                          {transaction.type === 'sent' ? '-' : '+'}£{transaction.amount}
                        </span>
                      </div>
                      <div className="text-gray-500">{new Date(transaction.created_at).toLocaleDateString()}</div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-500">No recent transactions</p>
                )}
              </div>
            </div>
          </div>

          {/* Management Actions */}
          <div className="space-y-4">
            {/* Status Update */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Update Status</h4>
              <form onSubmit={handleStatusUpdate} className="space-y-3">
                <select
                  value={statusForm.status}
                  onChange={(e) => setStatusForm(prev => ({ ...prev, status: e.target.value as 'ACTIVE' | 'SUSPENDED' | 'CLOSED' }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ACTIVE">Active</option>
                  <option value="SUSPENDED">Suspended</option>
                  <option value="CLOSED">Closed</option>
                </select>
                <input
                  type="text"
                  value={statusForm.reason}
                  onChange={(e) => setStatusForm(prev => ({ ...prev, reason: e.target.value }))}
                  placeholder="Reason for status change..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  disabled={user.id === currentUserId && statusForm.status !== 'ACTIVE'}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  Update Status
                </button>
              </form>
            </div>

            {/* Role Update */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Update Role</h4>
              <form onSubmit={handleRoleUpdate} className="space-y-3">
                <select
                  value={roleForm.role}
                  onChange={(e) => setRoleForm(prev => ({ ...prev, role: e.target.value as 'EMPLOYEE' | 'ADMIN' | 'FINANCE' }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="EMPLOYEE">Employee</option>
                  <option value="ADMIN">Admin</option>
                  <option value="FINANCE">Finance</option>
                </select>
                <input
                  type="text"
                  value={roleForm.reason}
                  onChange={(e) => setRoleForm(prev => ({ ...prev, reason: e.target.value }))}
                  placeholder="Reason for role change..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Update Role
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminPanel