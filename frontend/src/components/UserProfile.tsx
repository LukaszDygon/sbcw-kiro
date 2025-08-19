/**
 * UserProfile component for account settings and user information
 * Displays user details, account settings, and session information
 */
import React, { useState, useEffect } from 'react'
import { useAuth, useSession } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import { accountsService } from '../services/accounts'

interface AccountLimits {
  minimum_balance: string
  maximum_balance: string
  overdraft_limit: string
  overdraft_warning_threshold: string
}

interface AccountSummary {
  balance: string
  available_balance: string
  account_status: string
  limits: AccountLimits
}

const UserProfile: React.FC = () => {
  const { user, logout, updatePermissions } = useAuth()
  const { sessionInfo, getTimeUntilExpiry, extendSession } = useSession()
  const [accountSummary, setAccountSummary] = useState<AccountSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [extendingSession, setExtendingSession] = useState(false)

  useEffect(() => {
    const loadAccountData = async () => {
      try {
        setLoading(true)
        setError(null)

        const [summary] = await Promise.all([
          accountsService.getAccountSummary()
        ])

        setAccountSummary(summary)
      } catch (error: any) {
        console.error('Failed to load account data:', error)
        setError(error.message || 'Failed to load account data')
      } finally {
        setLoading(false)
      }
    }

    if (user) {
      loadAccountData()
    }
  }, [user])

  const handleExtendSession = async () => {
    try {
      setExtendingSession(true)
      await extendSession()
    } catch (error: any) {
      console.error('Failed to extend session:', error)
    } finally {
      setExtendingSession(false)
    }
  }

  const handleUpdatePermissions = async () => {
    try {
      await updatePermissions()
    } catch (error: any) {
      console.error('Failed to update permissions:', error)
    }
  }

  const formatCurrency = (amount: string) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP'
    }).format(parseFloat(amount))
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-GB', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatTimeRemaining = (milliseconds: number) => {
    const minutes = Math.floor(milliseconds / (1000 * 60))
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`
    }
    return `${minutes}m`
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-red-100 text-red-800'
      case 'FINANCE':
        return 'bg-blue-100 text-blue-800'
      case 'EMPLOYEE':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-100 text-green-800'
      case 'INACTIVE':
        return 'bg-gray-100 text-gray-800'
      case 'SUSPENDED':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" message="Loading profile..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Profile</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
            <div className="mt-4">
              <button
                onClick={() => window.location.reload()}
                className="bg-red-100 px-2 py-1 text-sm text-red-800 rounded hover:bg-red-200"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profile & Settings</h1>
        <p className="text-gray-600">
          Manage your account information and preferences
        </p>
      </div>

      {/* User Information */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">User Information</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name
            </label>
            <div className="text-sm text-gray-900 bg-gray-50 rounded-md px-3 py-2">
              {user?.name || 'Not available'}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <div className="text-sm text-gray-900 bg-gray-50 rounded-md px-3 py-2">
              {user?.email || 'Not available'}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Role
            </label>
            <div>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(user?.role || '')}`}>
                {user?.role || 'Not assigned'}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Account Status
            </label>
            <div>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(user?.account_status || '')}`}>
                {user?.account_status || 'Unknown'}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Member Since
            </label>
            <div className="text-sm text-gray-900 bg-gray-50 rounded-md px-3 py-2">
              {user?.created_at ? formatDate(user.created_at) : 'Not available'}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Last Login
            </label>
            <div className="text-sm text-gray-900 bg-gray-50 rounded-md px-3 py-2">
              {user?.last_login ? formatDate(user.last_login) : 'Not available'}
            </div>
          </div>
        </div>
      </div>

      {/* Account Summary */}
      {accountSummary && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Account Summary</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Balance
              </label>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(accountSummary.balance)}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Available Balance
              </label>
              <div className="text-2xl font-bold text-blue-600">
                {formatCurrency(accountSummary.available_balance)}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Overdraft Limit
              </label>
              <div className="text-sm text-gray-900">
                {formatCurrency(accountSummary.limits.overdraft_limit)}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Maximum Balance
              </label>
              <div className="text-sm text-gray-900">
                {formatCurrency(accountSummary.limits.maximum_balance)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Session Information */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Session Information</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {sessionInfo && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Session ID
                </label>
                <div className="text-sm text-gray-900 bg-gray-50 rounded-md px-3 py-2 font-mono">
                  {sessionInfo.session_id.substring(0, 16)}...
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Session Expires
                </label>
                <div className="text-sm text-gray-900 bg-gray-50 rounded-md px-3 py-2">
                  {formatDate(sessionInfo.expires_at)}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  IP Address
                </label>
                <div className="text-sm text-gray-900 bg-gray-50 rounded-md px-3 py-2 font-mono">
                  {sessionInfo.ip_address || 'Not available'}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Last Activity
                </label>
                <div className="text-sm text-gray-900 bg-gray-50 rounded-md px-3 py-2">
                  {formatDate(sessionInfo.last_activity)}
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Time Until Expiry
            </label>
            <div className="text-sm text-gray-900 bg-gray-50 rounded-md px-3 py-2">
              {formatTimeRemaining(getTimeUntilExpiry())}
            </div>
          </div>
        </div>

        <div className="mt-6 flex space-x-4">
          <button
            onClick={handleExtendSession}
            disabled={extendingSession}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {extendingSession ? (
              <>
                <LoadingSpinner size="small" className="mr-2" />
                Extending...
              </>
            ) : (
              'Extend Session'
            )}
          </button>

          <button
            onClick={handleUpdatePermissions}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Refresh Permissions
          </button>
        </div>
      </div>

      {/* Security Settings */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Security Settings</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Two-Factor Authentication</h4>
              <p className="text-sm text-gray-500">
                Additional security for your account via Microsoft Authenticator
              </p>
            </div>
            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
              Enabled via Microsoft
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Session Timeout</h4>
              <p className="text-sm text-gray-500">
                Automatic logout after period of inactivity
              </p>
            </div>
            <span className="text-sm text-gray-900">30 minutes</span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Login Notifications</h4>
              <p className="text-sm text-gray-500">
                Email notifications for new login sessions
              </p>
            </div>
            <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
              Enabled
            </span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Account Actions</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Sign Out</h4>
              <p className="text-sm text-gray-500">
                Sign out of your account on this device
              </p>
            </div>
            <button
              onClick={logout}
              className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
            >
              Sign Out
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Download Data</h4>
              <p className="text-sm text-gray-500">
                Export your transaction history and account data
              </p>
            </div>
            <button
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              disabled
            >
              Coming Soon
            </button>
          </div>
        </div>
      </div>

      {/* Help & Support */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Need Help?</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">IT Support</h4>
            <p className="text-sm text-gray-600">
              For technical issues or account problems
            </p>
            <a
              href="mailto:it-support@softbank.com"
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              it-support@softbank.com
            </a>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">Finance Team</h4>
            <p className="text-sm text-gray-600">
              For questions about transactions or limits
            </p>
            <a
              href="mailto:finance@softbank.com"
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              finance@softbank.com
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UserProfile