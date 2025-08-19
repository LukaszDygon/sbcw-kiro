/**
 * EventContribute component for contributing to events
 * Standalone component for event contribution with validation
 */
import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import EventsService from '../services/events'
import { EventAccount } from '../types'

interface ContributeFormData {
  amount: string
  note: string
}

const EventContribute: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  
  const [event, setEvent] = useState<EventAccount | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState<ContributeFormData>({
    amount: '',
    note: ''
  })
  const [contributing, setContributing] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  // Load event details
  useEffect(() => {
    if (eventId && user) {
      loadEvent()
    }
  }, [eventId, user])

  const loadEvent = async () => {
    if (!eventId) return

    try {
      setLoading(true)
      setError(null)

      const response = await EventsService.getEvent(eventId)
      setEvent(response.event)

      // Check if user can contribute
      if (!EventsService.canContributeToEvent(response.event, user!.id)) {
        setError('You cannot contribute to this event')
      }
    } catch (error: any) {
      console.error('Failed to load event:', error)
      setError(error.message || 'Failed to load event')
    } finally {
      setLoading(false)
    }
  }

  const updateForm = (field: keyof ContributeFormData, value: string) => {
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

    // Validate amount
    const amountValidation = EventsService.validateContributionAmount(form.amount)
    if (!amountValidation.valid) {
      errors.amount = amountValidation.error!
      isValid = false
    }

    // Validate note
    const noteValidation = EventsService.validateContributionNote(form.note)
    if (!noteValidation.valid) {
      errors.note = noteValidation.error!
      isValid = false
    }

    setValidationErrors(errors)
    return isValid
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm() || !eventId || !event) {
      return
    }

    try {
      setContributing(true)
      setError(null)

      await EventsService.contributeToEvent(eventId, {
        amount: form.amount,
        note: form.note || undefined
      })

      // Show success and redirect
      navigate(`/events/${eventId}`, { 
        state: { 
          message: `Successfully contributed ${EventsService.formatCurrency(form.amount)} to ${event.name}!` 
        }
      })
    } catch (error: any) {
      console.error('Failed to contribute:', error)
      setError(error.message || 'Failed to contribute to event')
    } finally {
      setContributing(false)
    }
  }

  const formatCurrency = (amount: string) => {
    return EventsService.formatCurrency(amount)
  }

  const getProgressPercentage = () => {
    if (!event) return 0
    return EventsService.getProgressPercentage(event) || 0
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-green-500'
    if (percentage >= 75) return 'bg-blue-500'
    if (percentage >= 50) return 'bg-yellow-500'
    return 'bg-gray-400'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
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
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={loadEvent}
                  className="bg-red-100 px-3 py-2 text-sm text-red-800 rounded hover:bg-red-200"
                >
                  Retry
                </button>
                <button
                  onClick={() => navigate('/events')}
                  className="bg-red-100 px-3 py-2 text-sm text-red-800 rounded hover:bg-red-200"
                >
                  Back to Events
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!event) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Event not found</h3>
        <p className="text-gray-500 mt-2">The event you're trying to contribute to doesn't exist.</p>
        <button
          onClick={() => navigate('/events')}
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          Back to Events
        </button>
      </div>
    )
  }

  const progressPercentage = getProgressPercentage()

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <button
          onClick={() => navigate(`/events/${eventId}`)}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Contribute to Event</h1>
          <p className="text-gray-600">{event.name}</p>
        </div>
      </div>

      {/* Event Summary */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Event Summary</h3>
            <p className="text-gray-600 mt-1">{event.description}</p>
          </div>

          {/* Progress */}
          {event.target_amount ? (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Progress</span>
                <span className="font-medium">
                  {formatCurrency(event.total_contributions)} of {formatCurrency(event.target_amount)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(progressPercentage)}`}
                  style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>{progressPercentage.toFixed(1)}% complete</span>
                <span>
                  {EventsService.getRemainingAmount(event) && 
                    `${formatCurrency(EventsService.getRemainingAmount(event)!)} remaining`
                  }
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center py-2">
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(event.total_contributions)}
              </div>
              <p className="text-sm text-gray-500">Total raised so far</p>
            </div>
          )}

          {/* Deadline warning */}
          {event.deadline && EventsService.isEventDeadlineApproaching(event) && (
            <div className="rounded-md bg-yellow-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">Deadline Approaching</h3>
                  <div className="mt-2 text-sm text-yellow-700">
                    {EventsService.formatTimeUntilDeadline(event)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Contribution Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Your Contribution</h3>

          <div className="space-y-6">
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
                Enter the amount you'd like to contribute (maximum: £10,000)
              </p>
            </div>

            {/* Note */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message <span className="text-gray-500">(Optional)</span>
              </label>
              <textarea
                rows={4}
                placeholder="Add a message with your contribution..."
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
                <span>Share why you're contributing or leave a message for others</span>
                <span>{form.note.length}/500</span>
              </div>
            </div>
          </div>
        </div>

        {/* Preview */}
        {form.amount && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Contribution Preview</h4>
            <div className="text-sm text-blue-800 space-y-1">
              <div>
                <strong>Amount:</strong> {formatCurrency(form.amount)}
              </div>
              <div>
                <strong>Event:</strong> {event.name}
              </div>
              {form.note && (
                <div>
                  <strong>Message:</strong> "{form.note}"
                </div>
              )}
              <div>
                <strong>Contributor:</strong> {user?.name}
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate(`/events/${eventId}`)}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={contributing || !form.amount.trim()}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {contributing ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Contributing...
              </>
            ) : (
              `Contribute ${form.amount ? formatCurrency(form.amount) : ''}`
            )}
          </button>
        </div>
      </form>

      {/* Help Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">How Contributions Work</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Your contribution will be deducted from your account balance immediately</li>
          <li>• All contributions are final and cannot be refunded</li>
          <li>• Your name and message (if provided) will be visible to other contributors</li>
          <li>• You'll receive confirmation once your contribution is processed</li>
          <li>• Event creators can close events and notify finance for fund disbursement</li>
        </ul>
      </div>
    </div>
  )
}

export default EventContribute