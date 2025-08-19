/**
 * SendMoney component with recipient selection and validation
 * Handles single and bulk money transfers with comprehensive validation
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import UserSearch, { User } from './UserSearch'
import { transactionsService } from '../services/transactions'
import { accountsService } from '../services/accounts'

interface Recipient {
  recipient_id: string
  recipient?: User | null
  amount: string
  category?: string
  note?: string
}

interface SendMoneyForm {
  recipients: Recipient[]
  isBulk: boolean
}

const SendMoney: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<SendMoneyForm>({
    recipients: [{ recipient_id: '', recipient: null, amount: '', category: '', note: '' }],
    isBulk: false
  })
  const [categories, setCategories] = useState<any[]>([])
  const [balance, setBalance] = useState<string>('0.00')
  const [loading, setLoading] = useState(false)
  const [loadingData, setLoadingData] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoadingData(true)
        const [categoriesResponse, balanceResponse] = await Promise.all([
          transactionsService.getCategories(),
          accountsService.getBalance()
        ])

        setCategories(categoriesResponse.categories || [])
        setBalance(balanceResponse.balance)
      } catch (error: any) {
        console.error('Failed to load initial data:', error)
        setError('Failed to load required data')
      } finally {
        setLoadingData(false)
      }
    }

    if (user) {
      loadInitialData()
    }
  }, [user])

  const addRecipient = () => {
    setForm(prev => ({
      ...prev,
      recipients: [...prev.recipients, { recipient_id: '', recipient: null, amount: '', category: '', note: '' }],
      isBulk: true
    }))
  }

  const removeRecipient = (index: number) => {
    if (form.recipients.length > 1) {
      setForm(prev => ({
        ...prev,
        recipients: prev.recipients.filter((_, i) => i !== index),
        isBulk: prev.recipients.length > 2
      }))
    }
  }

  const updateRecipient = (index: number, field: keyof Recipient, value: string) => {
    setForm(prev => ({
      ...prev,
      recipients: prev.recipients.map((recipient, i) => 
        i === index ? { ...recipient, [field]: value } : recipient
      )
    }))
    
    // Clear validation error for this field
    const errorKey = `recipients.${index}.${field}`
    if (validationErrors[errorKey]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[errorKey]
        return newErrors
      })
    }
  }

  const handleUserSelect = (index: number, selectedUser: User | null) => {
    setForm(prev => ({
      ...prev,
      recipients: prev.recipients.map((recipient, i) => 
        i === index ? { 
          ...recipient, 
          recipient_id: selectedUser?.id || '', 
          recipient: selectedUser 
        } : recipient
      )
    }))
    
    // Clear validation error for recipient selection
    const errorKey = `recipients.${index}.recipient_id`
    if (validationErrors[errorKey]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[errorKey]
        return newErrors
      })
    }
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    let isValid = true

    // Validate each recipient
    form.recipients.forEach((recipient, index) => {
      // Validate recipient selection
      if (!recipient.recipient_id) {
        errors[`recipients.${index}.recipient_id`] = 'Please select a recipient'
        isValid = false
      } else if (recipient.recipient_id === user?.id) {
        errors[`recipients.${index}.recipient_id`] = 'You cannot send money to yourself'
        isValid = false
      }

      // Validate amount
      if (!recipient.amount) {
        errors[`recipients.${index}.amount`] = 'Amount is required'
        isValid = false
      } else {
        const amount = parseFloat(recipient.amount)
        if (isNaN(amount) || amount <= 0) {
          errors[`recipients.${index}.amount`] = 'Amount must be greater than 0'
          isValid = false
        } else if (amount > 10000) {
          errors[`recipients.${index}.amount`] = 'Amount cannot exceed £10,000'
          isValid = false
        }
      }

      // Validate note length
      if (recipient.note && recipient.note.length > 500) {
        errors[`recipients.${index}.note`] = 'Note cannot exceed 500 characters'
        isValid = false
      }
    })

    // Check total amount against balance
    const totalAmount = form.recipients.reduce((sum, recipient) => {
      const amount = parseFloat(recipient.amount) || 0
      return sum + amount
    }, 0)

    if (totalAmount > parseFloat(balance)) {
      errors.general = 'Total amount exceeds your available balance'
      isValid = false
    }

    // Check for duplicate recipients
    const recipientIds = form.recipients.map(r => r.recipient_id).filter(Boolean)
    const duplicates = recipientIds.filter((id, index) => recipientIds.indexOf(id) !== index)
    if (duplicates.length > 0) {
      errors.general = 'Cannot send to the same recipient multiple times'
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

      if (form.isBulk && form.recipients.length > 1) {
        // Send bulk transfer
        await transactionsService.sendBulkMoney({
          recipients: form.recipients.map(r => ({
            recipient_id: r.recipient_id,
            amount: r.amount,
            category: r.category || undefined,
            note: r.note || undefined
          }))
        })
      } else {
        // Send single transfer
        const recipient = form.recipients[0]
        await transactionsService.sendMoney({
          recipient_id: recipient.recipient_id,
          amount: recipient.amount,
          category: recipient.category || undefined,
          note: recipient.note || undefined
        })
      }

      // Success - redirect to transactions
      navigate('/transactions/history', { 
        state: { message: 'Money sent successfully!' }
      })
    } catch (error: any) {
      console.error('Failed to send money:', error)
      setError(error.message || 'Failed to send money')
    } finally {
      setLoading(false)
    }
  }

  const getTotalAmount = () => {
    return form.recipients.reduce((sum, recipient) => {
      const amount = parseFloat(recipient.amount) || 0
      return sum + amount
    }, 0)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP'
    }).format(amount)
  }

  if (loadingData) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" message="Loading..." />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Send Money</h1>
        <p className="text-gray-600">
          Transfer money to other SoftBank employees
        </p>
      </div>

      {/* Balance Card */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Available Balance</h3>
            <p className="text-3xl font-bold text-green-600">{formatCurrency(parseFloat(balance))}</p>
          </div>
          {getTotalAmount() > 0 && (
            <div className="text-right">
              <div className="text-sm text-gray-500">Total to Send</div>
              <div className="text-2xl font-bold text-blue-600">
                {formatCurrency(getTotalAmount())}
              </div>
              <div className="text-sm text-gray-500">
                Remaining: {formatCurrency(parseFloat(balance) - getTotalAmount())}
              </div>
            </div>
          )}
        </div>
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

      {/* General Validation Error */}
      {validationErrors.general && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-700">{validationErrors.general}</div>
        </div>
      )}

      {/* Send Money Form */}
      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-gray-900">
              {form.isBulk ? 'Recipients' : 'Recipient'}
            </h3>
            <button
              type="button"
              onClick={addRecipient}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Recipient
            </button>
          </div>

          <div className="space-y-6">
            {form.recipients.map((recipient, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-md font-medium text-gray-900">
                    Recipient {index + 1}
                  </h4>
                  {form.recipients.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRecipient(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Recipient *
                    </label>
                    <UserSearch
                      onUserSelect={(selectedUser) => handleUserSelect(index, selectedUser)}
                      selectedUser={recipient.recipient}
                      placeholder="Search for a recipient..."
                      excludeSelf={true}
                      className={validationErrors[`recipients.${index}.recipient_id`] ? 'border-red-300' : ''}
                    />
                    {validationErrors[`recipients.${index}.recipient_id`] && (
                      <p className="mt-1 text-sm text-red-600">
                        {validationErrors[`recipients.${index}.recipient_id`]}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Amount (£) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      max="10000"
                      placeholder="0.00"
                      value={recipient.amount}
                      onChange={(e) => updateRecipient(index, 'amount', e.target.value)}
                      className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                        validationErrors[`recipients.${index}.amount`] 
                          ? 'border-red-300' 
                          : 'border-gray-300'
                      }`}
                    />
                    {validationErrors[`recipients.${index}.amount`] && (
                      <p className="mt-1 text-sm text-red-600">
                        {validationErrors[`recipients.${index}.amount`]}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Category
                    </label>
                    <select
                      value={recipient.category || ''}
                      onChange={(e) => updateRecipient(index, 'category', e.target.value)}
                      className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    >
                      <option value="">Select category (optional)</option>
                      {categories.map(category => (
                        <option key={category.id} value={category.name}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Note
                    </label>
                    <input
                      type="text"
                      placeholder="Optional note"
                      maxLength={500}
                      value={recipient.note || ''}
                      onChange={(e) => updateRecipient(index, 'note', e.target.value)}
                      className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                        validationErrors[`recipients.${index}.note`] 
                          ? 'border-red-300' 
                          : 'border-gray-300'
                      }`}
                    />
                    {validationErrors[`recipients.${index}.note`] && (
                      <p className="mt-1 text-sm text-red-600">
                        {validationErrors[`recipients.${index}.note`]}
                      </p>
                    )}
                    {recipient.note && (
                      <p className="mt-1 text-sm text-gray-500">
                        {recipient.note.length}/500 characters
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Summary */}
        {getTotalAmount() > 0 && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">
                Total Amount ({form.recipients.length} recipient{form.recipients.length > 1 ? 's' : ''})
              </span>
              <span className="text-lg font-bold text-gray-900">
                {formatCurrency(getTotalAmount())}
              </span>
            </div>
            <div className="flex justify-between items-center mt-2">
              <span className="text-sm text-gray-500">Remaining Balance</span>
              <span className={`text-sm font-medium ${
                parseFloat(balance) - getTotalAmount() >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(parseFloat(balance) - getTotalAmount())}
              </span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading || getTotalAmount() === 0}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <LoadingSpinner size="small" className="mr-2" />
                Sending...
              </>
            ) : (
              `Send ${formatCurrency(getTotalAmount())}`
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

export default SendMoney