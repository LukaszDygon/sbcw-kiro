/**
 * EventDetails component for viewing event details and contributing
 * Shows event information, progress, contributors, and contribution interface
 */
import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAuth } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import EventsService from '../services/events'
import { EventAccount, EventStatus } from '../types'

interface EventContribution {
  id: string
  contributor_id: string
  contributor_name: string
  amount: string
  note?: string
  created_at: string
}

interface ContributeFormData {
  amount: string
  note: string
}

const EventDetails: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  
  const [event, setEvent] = useState<EventAccount | null>(null)
  const [contributions, setContributions] = useState<EventContribution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showContributeForm, setShowContributeForm] = useState(false)
  const [contributeForm, setContributeForm] = useState<ContributeFormData>({
    amount: '',
    note: ''
  })
  const [contributing, setContributing] = useState(false)
  const [contributeError, setContributeError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // Load event details and contributions
  useEffect(() => {
    if (eventId && user) {
      loadEventDetails()
    }
  }, [eventId, user])

  const loadEventDetails = async () => {
    if (!eventId) return

    try {
      setLoading(true)
      setError(null)

      const [eventResponse, contributionsResponse] = await Promise.all([
        EventsService.getEvent(eventId),
        EventsService.getEventContributions(eventId)
      ])

      setEvent(eventResponse.event)
      setContributions(contributionsResponse.contributions)
    } catch (error: any) {
      console.error('Failed to load event details:', error)
      setError(error.message || 'Failed to load event details')
    } finally {
      setLoading(false)
    }
  }

  const handleContribute = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!eventId || !event) return

    // Validate form
    const amountValidation = EventsService.validateContributionAmount(contributeForm.amount)
    const noteValidation = EventsService.validateContributionNote(contributeForm.note)

    if (!amountValidation.valid) {
      setContributeError(amountValidation.error!)
      return
    }

    if (!noteValidation.valid) {
      setContributeError(noteValidation.error!)
      return
    }

    try {
      setContributing(true)
      setContributeError(null)

      const response = await EventsService.contributeToEvent(eventId, {
        amount: contributeForm.amount,
        note: contributeForm.note || undefined
      })

      // Update event with new contribution data
      setEvent(response.event)
      
      // Reload contributions to show the new one
      const contributionsResponse = await EventsService.getEventContributions(eventId)
      setContributions(contributionsResponse.contributions)

      // Reset form and hide it
      setContributeForm({ amount: '', note: '' })
      setShowContributeForm(false)

      // Show success message (you might want to add a toast notification here)
      alert('Contribution successful!')
    } catch (error: any) {
      console.error('Failed to contribute:', error)
      setContributeError(error.message || 'Failed to contribute to event')
    } finally {
      setContributing(false)
    }
  }

  const handleCloseEvent = async () => {
    if (!eventId || !event) return

    if (!confirm('Are you sure you want to close this event? This action cannot be undone.')) {
      return
    }

    try {
      setActionLoading('close')
      const response = await EventsService.closeEvent(eventId)
      setEvent(response.event)
      alert(response.message)
    } catch (error: any) {
      console.error('Failed to close event:', error)
      alert(error.message || 'Failed to close event')
    } finally {
      setActionLoading(null)
    }
  }

  const handleCancelEvent = async () => {
    if (!eventId || !event) return

    if (!confirm('Are you sure you want to cancel this event? This action cannot be undone.')) {
      return
    }

    try {
      setActionLoading('cancel')
      const response = await EventsService.cancelEvent(eventId)
      setEvent(response.event)
      alert(response.message)
    } catch (error: any) {
      console.error('Failed to cancel event:', error)
      alert(error.message || 'Failed to cancel event')
    } finally {
      setActionLoading(null)
    }
  }

  const formatCurrency = (amount: string) => {
    return EventsService.formatCurrency(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
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

  const getStatusColor = (status: EventStatus) => {
    switch (status) {
      case EventStatus.ACTIVE:
        return 'text-green-600 bg-green-100'
      case EventStatus.CLOSED:
        return 'text-blue-600 bg-blue-100'
      case EventStatus.CANCELLED:
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const canContribute = () => {
    return event && user && EventsService.canContributeToEvent(event, user.id)
  }

  const canCloseEvent = () => {
    return event && user && EventsService.canCloseEvent(event, user.id)
  }

  const canCancelEvent = () => {
    return event && user && EventsService.canCancelEvent(event, user.id)
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
      <div className="max-w-4xl mx-auto">
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Event</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={loadEventDetails}
                  className="bg-red-100 px-3 py-2 text-sm text-red-800 rounded hover:bg-red-200"
                >
                  Retry
                </button>
                <Link
                  to="/events"
                  className="bg-red-100 px-3 py-2 text-sm text-red-800 rounded hover:bg-red-200"
                >
                  Back to Events
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!event) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Event not found</h3>
        <p className="text-gray-500 mt-2">The event you're looking for doesn't exist or has been removed.</p>
        <Link
          to="/events"
          className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          Back to Events
        </Link>
      </div>
    )
  }

  const progressPercentage = getProgressPercentage()
  const timeUntilDeadline = EventsService.formatTimeUntilDeadline(event)

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/events"
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{event.name}</h1>
            <p className="text-gray-600">Created by {event.creator_name}</p>
          </div>
        </div>
        <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(event.status)}`}>
          {event.status.toLowerCase()}
        </span>
      </div>

      {/* Event Details Card */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Event Info */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Description</h3>
                <p className="text-gray-600 whitespace-pre-wrap">{event.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Created</h4>
                  <p className="text-sm text-gray-600">{formatDate(event.created_at)}</p>
                </div>
                {event.deadline && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Deadline</h4>
                    <p className={`text-sm ${
                      EventsService.isEventDeadlinePassed(event) ? 'text-red-600' : 
                      EventsService.isEventDeadlineApproaching(event) ? 'text-yellow-600' : 'text-gray-600'
                    }`}>
                      {timeUntilDeadline}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column - Progress */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-3">Progress</h3>
                
                {event.target_amount ? (
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Raised</span>
                      <span className="font-medium">
                        {formatCurrency(event.total_contributions)} of {formatCurrency(event.target_amount)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all duration-300 ${getProgressColor(progressPercentage)}`}
                        style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-sm text-gray-500">
                      <span>{progressPercentage.toFixed(1)}% complete</span>
                      <span>
                        {EventsService.getRemainingAmount(event) && 
                          `${formatCurrency(EventsService.getRemainingAmount(event)!)} remaining`
                        }
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <div className="text-3xl font-bold text-green-600">
                      {formatCurrency(event.total_contributions)}
                    </div>
                    <p className="text-sm text-gray-500">Total raised</p>
                  </div>
                )}

                <div className="mt-4 text-center text-sm text-gray-500">
                  {contributions.length} contribution{contributions.length !== 1 ? 's' : ''} from{' '}
                  {new Set(contributions.map(c => c.contributor_id)).size} contributor{new Set(contributions.map(c => c.contributor_id)).size !== 1 ? 's' : ''}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                {canContribute() && (
                  <button
                    onClick={() => setShowContributeForm(true)}
                    className="w-full px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Contribute to Event
                  </button>
                )}

                {canCloseEvent() && (
                  <button
                    onClick={handleCloseEvent}
                    disabled={actionLoading === 'close'}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    {actionLoading === 'close' ? 'Closing...' : 'Close Event'}
                  </button>
                )}

                {canCancelEvent() && (
                  <button
                    onClick={handleCancelEvent}
                    disabled={actionLoading === 'cancel'}
                    className="w-full px-4 py-2 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-white hover:bg-red-50 disabled:opacity-50"
                  >
                    {actionLoading === 'cancel' ? 'Cancelling...' : 'Cancel Event'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Contribute Form Modal */}
      {showContributeForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Contribute to {event.name}</h3>
              
              {contributeError && (
                <div className="mb-4 rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-700">{contributeError}</div>
                </div>
              )}

              <form onSubmit={handleContribute} className="space-y-4">
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
                    value={contributeForm.amount}
                    onChange={(e) => setContributeForm(prev => ({ ...prev, amount: e.target.value }))}
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Note (Optional)
                  </label>
                  <textarea
                    rows={3}
                    placeholder="Add a message with your contribution..."
                    maxLength={500}
                    value={contributeForm.note}
                    onChange={(e) => setContributeForm(prev => ({ ...prev, note: e.target.value }))}
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  <div className="mt-1 text-xs text-gray-500 text-right">
                    {contributeForm.note.length}/500
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowContributeForm(false)
                      setContributeForm({ amount: '', note: '' })
                      setContributeError(null)
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={contributing || !contributeForm.amount}
                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    {contributing ? 'Contributing...' : `Contribute ${contributeForm.amount ? formatCurrency(contributeForm.amount) : ''}`}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Contributors List */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Contributors</h3>
        </div>
        
        {contributions.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {contributions.map((contribution) => (
              <div key={contribution.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            {contribution.contributor_name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-gray-900">
                          {contribution.contributor_name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(contribution.created_at)}
                        </p>
                      </div>
                    </div>
                    {contribution.note && (
                      <p className="mt-2 text-sm text-gray-600 ml-11">
                        "{contribution.note}"
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-green-600">
                      {formatCurrency(contribution.amount)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-6 py-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No contributions yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Be the first to contribute to this event!
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default EventDetails