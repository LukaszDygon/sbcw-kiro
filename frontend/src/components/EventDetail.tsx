/**
 * EventDetail component for viewing event details and making contributions
 * Shows event progress, contributor information, and contribution interface
 */
import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import { eventsService } from '../services/events'

interface Event {
  id: string
  name: string
  description: string
  target_amount?: string
  current_amount: string
  progress_percentage: number
  creator_id: string
  creator_name: string
  status: string
  created_at: string
  deadline?: string
  contribution_count: number
  unique_contributors: number
}

interface Contribution {
  id: string
  contributor_id: string
  contributor_name: string
  amount: string
  note?: string
  created_at: string
}

interface ContributionForm {
  amount: string
  note: string
}

const EventDetail: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [event, setEvent] = useState<Event | null>(null)
  const [contributions, setContributions] = useState<Contribution[]>([])
  const [loading, setLoading] = useState(true)
  const [contributionLoading, setContributionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showContributeForm, setShowContributeForm] = useState(false)
  const [contributionForm, setContributionForm] = useState<ContributionForm>({
    amount: '',
    note: ''
  })
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const loadEventData = async () => {
      if (!eventId) return

      try {
        setLoading(true)
        setError(null)

        const [eventResponse, contributionsResponse] = await Promise.all([
          eventsService.getEventById(eventId),
          eventsService.getEventContributions(eventId)
        ])

        setEvent(eventResponse.event)
        setContributions(contributionsResponse.contributions)
      } catch (error: any) {
        console.error('Failed to load event data:', error)
        setError(error.message || 'Failed to load event data')
      } finally {
        setLoading(false)
      }
    }

    loadEventData()
  }, [eventId])

  const updateContributionForm = (field: keyof ContributionForm, value: string) => {
    setContributionForm(prev => ({ ...prev, [field]: value }))
    
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  const validateContribution = (): boolean => {
    const errors: Record<string, string> = {}
    let isValid = true

    // Validate amount
    if (!contributionForm.amount) {
      errors.amount = 'Amount is required'
      isValid = false
    } else {
      const amount = parseFloat(contributionForm.amount)
      if (isNaN(amount) || amount <= 0) {
        errors.amount = 'Amount must be greater than 0'
        isValid = false
      } else if (amount > 10000) {
        errors.amount = 'Amount cannot exceed £10,000'
        isValid = false
      }
    }

    // Validate note length
    if (contributionForm.note && contributionForm.note.length > 500) {
      errors.note = 'Note cannot exceed 500 characters'
      isValid = false
    }

    setValidationErrors(errors)
    return isValid
  }

  const handleContribute = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateContribution() || !eventId) {
      return
    }

    try {
      setContributionLoading(true)
      setError(null)

      await eventsService.contributeToEvent(eventId, {
        amount: contributionForm.amount,
        note: contributionForm.note || undefined
      })

      // Reload event data to show updated progress
      const [eventResponse, contributionsResponse] = await Promise.all([
        eventsService.getEventById(eventId),
        eventsService.getEventContributions(eventId)
      ])

      setEvent(eventResponse.event)
      setContributions(contributionsResponse.contributions)
      
      // Reset form and hide it
      setContributionForm({ amount: '', note: '' })
      setShowContributeForm(false)
      
    } catch (error: any) {
      console.error('Failed to contribute:', error)
      setError(error.message || 'Failed to process contribution')
    } finally {
      setContributionLoading(false)
    }
  }

  const handleCloseEvent = async () => {
    if (!eventId || !window.confirm('Are you sure you want to close this event? This action cannot be undone.')) {
      return
    }

    try {
      await eventsService.closeEvent(eventId)
      navigate('/events/my-events', { 
        state: { message: 'Event closed successfully!' }
      })
    } catch (error: any) {
      console.error('Failed to close event:', error)
      setError(error.message || 'Failed to close event')
    }
  }

  const formatCurrency = (amount: string) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP'
    }).format(parseFloat(amount))
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-green-500'
    if (percentage >= 75) return 'bg-blue-500'
    if (percentage >= 50) return 'bg-yellow-500'
    return 'bg-gray-400'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'text-green-600 bg-green-100'
      case 'COMPLETED':
        return 'text-blue-600 bg-blue-100'
      case 'CANCELLED':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const isExpired = (deadline?: string) => {
    if (!deadline) return false
    return new Date(deadline) < new Date()
  }

  const canContribute = () => {
    return event?.status === 'ACTIVE' && !isExpired(event.deadline)
  }

  const canManageEvent = () => {
    return event?.creator_id === user?.id || user?.role === 'ADMIN' || user?.role === 'FINANCE'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" message="Loading event..." />
      </div>
    )
  }

  if (error || !event) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Event</h3>
            <div className="mt-2 text-sm text-red-700">{error || 'Event not found'}</div>
            <div className="mt-4 space-x-2">
              <button
                onClick={() => window.location.reload()}
                className="bg-red-100 px-2 py-1 text-sm text-red-800 rounded hover:bg-red-200"
              >
                Retry
              </button>
              <button
                onClick={() => navigate('/events')}
                className="bg-gray-100 px-2 py-1 text-sm text-gray-800 rounded hover:bg-gray-200"
              >
                Back to Events
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
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{event.name}</h1>
          <p className="text-gray-600">
            Created by {event.creator_name} on {formatDate(event.created_at)}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(event.status)}`}>
            {event.status.toLowerCase()}
          </span>
          {canManageEvent() && event.status === 'ACTIVE' && (
            <button
              onClick={handleCloseEvent}
              className="inline-flex items-center px-3 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
            >
              Close Event
            </button>
          )}
        </div>
      </div>

      {/* Event Details */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Event Details</h3>
        
        <div className="prose max-w-none">
          <p className="text-gray-700">{event.description}</p>
        </div>

        {event.deadline && (
          <div className={`mt-4 flex items-center text-sm ${
            isExpired(event.deadline) ? 'text-red-600' : 'text-gray-600'
          }`}>
            <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {isExpired(event.deadline) ? (
              <span className="font-medium">Deadline passed: {formatDate(event.deadline)}</span>
            ) : (
              <span>Deadline: {formatDate(event.deadline)}</span>
            )}
          </div>
        )}
      </div>

      {/* Progress Section */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Progress</h3>
        
        {event.target_amount ? (
          <div className="space-y-4">
            <div className="flex justify-between items-end">
              <div>
                <div className="text-3xl font-bold text-green-600">
                  {formatCurrency(event.current_amount)}
                </div>
                <div className="text-sm text-gray-500">
                  of {formatCurrency(event.target_amount)} target
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  {event.progress_percentage.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-500">complete</div>
              </div>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className={`h-4 rounded-full transition-all duration-500 ${getProgressColor(event.progress_percentage)}`}
                style={{ width: `${Math.min(event.progress_percentage, 100)}%` }}
              />
            </div>
            
            <div className="flex justify-between text-sm text-gray-600">
              <span>
                {event.unique_contributors} contributor{event.unique_contributors !== 1 ? 's' : ''}
              </span>
              <span>
                {event.contribution_count} contribution{event.contribution_count !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        ) : (
          <div className="text-center space-y-2">
            <div className="text-3xl font-bold text-green-600">
              {formatCurrency(event.current_amount)}
            </div>
            <div className="text-sm text-gray-500">
              raised from {event.unique_contributors} contributor{event.unique_contributors !== 1 ? 's' : ''}
            </div>
          </div>
        )}

        {/* Contribute Button */}
        {canContribute() && (
          <div className="mt-6">
            {!showContributeForm ? (
              <button
                onClick={() => setShowContributeForm(true)}
                className="w-full px-4 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                Contribute to This Event
              </button>
            ) : (
              <form onSubmit={handleContribute} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contribution Amount (£) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max="10000"
                    placeholder="0.00"
                    value={contributionForm.amount}
                    onChange={(e) => updateContributionForm('amount', e.target.value)}
                    className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                      validationErrors.amount ? 'border-red-300' : 'border-gray-300'
                    }`}
                  />
                  {validationErrors.amount && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.amount}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Note (Optional)
                  </label>
                  <textarea
                    rows={2}
                    placeholder="Add a message with your contribution"
                    maxLength={500}
                    value={contributionForm.note}
                    onChange={(e) => updateContributionForm('note', e.target.value)}
                    className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                      validationErrors.note ? 'border-red-300' : 'border-gray-300'
                    }`}
                  />
                  {validationErrors.note && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.note}</p>
                  )}
                  <p className="mt-1 text-sm text-gray-500">
                    {contributionForm.note.length}/500 characters
                  </p>
                </div>

                <div className="flex space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowContributeForm(false)
                      setContributionForm({ amount: '', note: '' })
                      setValidationErrors({})
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={contributionLoading || !contributionForm.amount}
                    className="flex-1 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {contributionLoading ? (
                      <>
                        <LoadingSpinner size="small" className="mr-2" />
                        Contributing...
                      </>
                    ) : (
                      `Contribute ${contributionForm.amount ? formatCurrency(contributionForm.amount) : ''}`
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* Event Status Messages */}
        {!canContribute() && (
          <div className="mt-6 p-4 bg-gray-50 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-gray-600">
                  {event.status !== 'ACTIVE' 
                    ? `This event is ${event.status.toLowerCase()} and no longer accepting contributions.`
                    : 'This event has expired and is no longer accepting contributions.'
                  }
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Contributors */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Contributors ({contributions.length})
        </h3>
        
        {contributions.length > 0 ? (
          <div className="space-y-4">
            {contributions.map((contribution) => (
              <div key={contribution.id} className="flex items-start justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">
                          {contribution.contributor_name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-3">
                      <div className="text-sm font-medium text-gray-900">
                        {contribution.contributor_name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDate(contribution.created_at)}
                      </div>
                    </div>
                  </div>
                  {contribution.note && (
                    <div className="mt-2 text-sm text-gray-600">
                      "{contribution.note}"
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold text-green-600">
                    {formatCurrency(contribution.amount)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <p className="mt-2">No contributions yet</p>
            <p className="text-sm">Be the first to contribute to this event!</p>
          </div>
        )}
      </div>

      {/* Back Button */}
      <div className="flex justify-start">
        <button
          onClick={() => navigate('/events')}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Events
        </button>
      </div>
    </div>
  )
}

export default EventDetail