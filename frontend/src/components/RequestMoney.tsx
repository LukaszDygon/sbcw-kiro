/**
 * RequestMoney component for creating and managing money requests
 * Handles request creation with validation and expiration settings
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import { moneyRequestsService } from '../services/moneyRequests'

interface User {
  id: string
  name: string
  email: string
  department?: string
}

interface RequestForm {
  recipient_id: string
  amount: string
  note: string
  expires_in_days: number
}

const RequestMoney: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<RequestForm>({
    recipient_id: '',
    amount: '',
    note: '',
    expires_in_days: 7
  })
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Load users
  useEffect(() => {
    const loadUsers = async () => {
      try {
        setLoadingUsers(true)
        // Note: We'll need to implement a users endpoint
        // For now, using placeholder data
        setUsers([])
      } catch (error: any) {
        console.error('Failed to load users:', error)
        setError('Failed to load users')
      } finally {
        setLoadingUsers(false)
      }
    }

    if (user) {
      loadUsers()
    }
  }, [user])

  const updateForm = (field: keyof RequestForm, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }))
    
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    let isValid = true

    // Validate recipient
    if (!form.recipient_id) {
      errors.recipient_id = 'Please select a recipient'
      isValid = false
    } else if (form.recipient_id === user?.id) {
      errors.recipient_id = 'You cannot request money from yourself'
      isValid = false
    }

    // Validate amount
    if (!form.amount) {
      errors.amount = 'Amount is required'
      isValid = false
    } else {
      const amount = parseFloat(form.amount)
      if (isNaN(amount) || amount <= 0) {
        errors.amount = 'Amount must be greater than 0'
        isValid = false
      } else if (amount > 10000) {
        errors.amount = 'Amount cannot exceed £10,000'
        isValid = false
      }
    }

    // Validate note length
    if (form.note && form.note.length > 500) {
      errors.note = 'Note cannot exceed 500 characters'
      isValid = false
    }

    // Validate expiration
    if (form.expires_in_days < 1 || form.expires_in_days > 30) {
      errors.expires_in_days = 'Expiration must be between 1 and 30 days'
      isValid = false
    }

    setValidationErrors(errors)
    return isValid
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    try {
      setLoading(true)
      setError(null)

      await moneyRequestsService.createRequest({
        recipient_id: form.recipient_id,
        amount: form.amount,
        note: form.note || undefined,
        expires_in_days: form.expires_in_days
      })

      // Success - redirect to requests
      navigate('/money-requests/sent', { 
        state: { message: 'Money request sent successfully!' }
      })
    } catch (error: any) {
      console.error('Failed to create request:', error)
      setError(error.message || 'Failed to create money request')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: string) => {
    const num = parseFloat(amount) || 0
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP'
    }).format(num)
  }

  const getExpirationDate = () => {
    const date = new Date()
    date.setDate(date.getDate() + form.expires_in_days)
    return date.toLocaleDateString('en-GB', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (loadingUsers) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" message="Loading..." />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Request Money</h1>
        <p className="text-gray-600">
          Request money from other SoftBank employees
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Request Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Request Details</h3>

          <div className="space-y-6">
            {/* Recipient Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Request From *
              </label>
              <select
                value={form.recipient_id}
                onChange={(e) => updateForm('recipient_id', e.target.value)}
                className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  validationErrors.recipient_id ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value="">Select a person to request from</option>
                {users.map(u => (
                  <option key={u.id} value={u.id} disabled={u.id === user?.id}>
                    {u.name} ({u.email})
                    {u.department && ` - ${u.department}`}
                  </option>
                ))}
              </select>
              {validationErrors.recipient_id && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.recipient_id}</p>
              )}
            </div>

            {/* Amount */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Amount (£) *
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="10000"
                  placeholder="0.00"
                  value={form.amount}
                  onChange={(e) => updateForm('amount', e.target.value)}
                  className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                    validationErrors.amount ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {form.amount && (
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <span className="text-gray-500 sm:text-sm">
                      {formatCurrency(form.amount)}
                    </span>
                  </div>
                )}
              </div>
              {validationErrors.amount && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.amount}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Maximum amount: £10,000
              </p>
            </div>

            {/* Note */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Note
              </label>
              <textarea
                rows={3}
                placeholder="Optional note explaining what this request is for"
                maxLength={500}
                value={form.note}
                onChange={(e) => updateForm('note', e.target.value)}
                className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  validationErrors.note ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {validationErrors.note && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.note}</p>
              )}
              <div className="mt-1 flex justify-between text-sm text-gray-500">
                <span>Help the recipient understand what this request is for</span>
                <span>{form.note.length}/500</span>
              </div>
            </div>

            {/* Expiration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expires In
              </label>
              <select
                value={form.expires_in_days}
                onChange={(e) => updateForm('expires_in_days', parseInt(e.target.value))}
                className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  validationErrors.expires_in_days ? 'border-red-300' : 'border-gray-300'
                }`}
              >
                <option value={1}>1 day</option>
                <option value={3}>3 days</option>
                <option value={7}>1 week (recommended)</option>
                <option value={14}>2 weeks</option>
                <option value={30}>1 month</option>
              </select>
              {validationErrors.expires_in_days && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.expires_in_days}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Request will expire on {getExpirationDate()}
              </p>
            </div>
          </div>
        </div>

        {/* Preview */}
        {form.recipient_id && form.amount && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Request Preview</h4>
            <div className="text-sm text-blue-800">
              <p>
                You are requesting <strong>{formatCurrency(form.amount)}</strong> from{' '}
                <strong>
                  {users.find(u => u.id === form.recipient_id)?.name || 'Selected recipient'}
                </strong>
              </p>
              {form.note && (
                <p className="mt-1">
                  <strong>Note:</strong> {form.note}
                </p>
              )}
              <p className="mt-1">
                <strong>Expires:</strong> {getExpirationDate()}
              </p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/money-requests')}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading || !form.recipient_id || !form.amount}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <LoadingSpinner size="small" className="mr-2" />
                Sending Request...
              </>
            ) : (
              'Send Request'
            )}
          </button>
        </div>
      </form>

      {/* Help Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">How Money Requests Work</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• The recipient will receive a notification about your request</li>
          <li>• They can approve or decline the request</li>
          <li>• If approved, the money will be transferred automatically</li>
          <li>• Requests expire after the selected time period</li>
          <li>• You can cancel pending requests at any time</li>
        </ul>
      </div>
    </div>
  )
}

export default RequestMoney