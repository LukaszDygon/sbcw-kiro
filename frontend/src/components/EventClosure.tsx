/**
 * EventClosure component for closing events by authorized users
 * Provides interface for event creators and finance team to close events
 */
import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import EventsService from '../services/events'
import { EventAccount, UserRole } from '../types'

interface EventContribution {
  id: string
  contributor_id: string
  contributor_name: string
  amount: string
  note?: string
  created_at: string
}

const EventClosure: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()
  
  const [event, setEvent] = useState<EventAccount | null>(null)
  const [contributions, setContributions] = useState<EventContribution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [closing, setClosing] = useState(false)
  const [cancelling, setCancelling] = useState(false)

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

      // Check if user has permission to close/cancel event
      const canClose = EventsService.canCloseEvent(eventResponse.event, user!.id)
      const canCancel = EventsService.canCancelEvent(eventResponse.event, user!.id)
      const isFinanceTeam = user!.role === UserRole.FINANCE

      if (!canClose && !canCancel && !isFinanceTeam) {
        setError('You do not have permission to manage this event')
      }
    } catch (error: any) {
      console.error('Failed to load event details:', error)
      setError(error.message || 'Failed to load event details')
    } finally {
      setLoading(false)
    }
  }

  const handleCloseEvent = async () => {
    if (!eventId || !event) return

    const confirmMessage = `Are you sure you want to close "${event.name}"?\n\n` +
      `This will:\n` +
      `• Stop accepting new contributions\n` +
      `• Notify the finance team for fund disbursement\n` +
      `• Mark the event as completed\n\n` +
      `This action cannot be undone.`

    if (!confirm(confirmMessage)) {
      return
    }

    try {
      setClosing(true)
      const response = await EventsService.closeEvent(eventId)
      
      // Show success message and redirect
      navigate(`/events/${eventId}`, { 
        state: { 
          message: response.message || 'Event closed successfully. Finance team has been notified.' 
        }
      })
    } catch (error: any) {
      console.error('Failed to close event:', error)
      setError(error.message || 'Failed to close event')
    } finally {
      setClosing(false)
    }
  }

  const handleCancelEvent = async () => {
    if (!eventId || !event) return

    const confirmMessage = `Are you sure you want to cancel "${event.name}"?\n\n` +
      `This will:\n` +
      `• Permanently cancel the event\n` +
      `• Stop accepting contributions\n` +
      `• Mark the event as cancelled\n\n` +
      `This action cannot be undone.`

    if (!confirm(confirmMessage)) {
      return
    }

    try {
      setCancelling(true)
      const response = await EventsService.cancelEvent(eventId)
      
      // Show success message and redirect
      navigate(`/events/${eventId}`, { 
        state: { 
          message: response.message || 'Event cancelled successfully.' 
        }
      })
    } catch (error: any) {
      console.error('Failed to cancel event:', error)
      setError(error.message || 'Failed to cancel event')
    } finally {
      setCancelling(false)
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

  const canCloseEvent = () => {
    return event && user && (
      EventsService.canCloseEvent(event, user.id) || 
      user.role === UserRole.FINANCE
    )
  }

  const canCancelEvent = () => {
    return event && user && (
      EventsService.canCancelEvent(event, user.id) || 
      user.role === UserRole.FINANCE
    )
  }

  const getTotalUniqueContributors = () => {
    return new Set(contributions.map(c => c.contributor_id)).size
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
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={loadEventDetails}
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
      <div className="max-w-4xl mx-auto text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">Event not found</h3>
        <p className="text-gray-500 mt-2">The event you're looking for doesn't exist or has been removed.</p>
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
  const uniqueContributors = getTotalUniqueContributors()

  return (
    <div className="max-w-4xl mx-auto space-y-6">
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
          <h1 className="text-2xl font-bold text-gray-900">Manage Event</h1>
          <p className="text-gray-600">{event.name}</p>
        </div>
      </div>

      {/* Event Summary */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Event Summary</h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Event Details */}
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Description</h4>
              <p className="text-sm text-gray-600 mt-1">{event.description}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-medium text-gray-900">Created</h4>
                <p className="text-sm text-gray-600">{formatDate(event.created_at)}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-900">Creator</h4>
                <p className="text-sm text-gray-600">{event.creator_name}</p>
              </div>
            </div>

            {event.deadline && (
              <div>
                <h4 className="text-sm font-medium text-gray-900">Deadline</h4>
                <p className={`text-sm ${
                  EventsService.isEventDeadlinePassed(event) ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {EventsService.formatTimeUntilDeadline(event)}
                </p>
              </div>
            )}
          </div>

          {/* Financial Summary */}
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Financial Summary</h4>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Total Raised</span>
                  <span className="text-sm font-medium text-green-600">
                    {formatCurrency(event.total_contributions)}
                  </span>
                </div>

                {event.target_amount && (
                  <>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Target Amount</span>
                      <span className="text-sm font-medium">
                        {formatCurrency(event.target_amount)}
                      </span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Progress</span>
                      <span className="text-sm font-medium">
                        {progressPercentage.toFixed(1)}%
                      </span>
                    </div>

                    {EventsService.getRemainingAmount(event) && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Remaining</span>
                        <span className="text-sm font-medium">
                          {formatCurrency(EventsService.getRemainingAmount(event)!)}
                        </span>
                      </div>
                    )}
                  </>
                )}

                <div className="border-t pt-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Contributors</span>
                    <span className="text-sm font-medium">{uniqueContributors}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Contributions</span>
                    <span className="text-sm font-medium">{contributions.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Event Actions</h3>
        
        <div className="space-y-4">
          {/* Close Event */}
          {canCloseEvent() && (
            <div className="border border-blue-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-900">Close Event</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Mark this event as complete and notify the finance team for fund disbursement. 
                    No new contributions will be accepted after closing.
                  </p>
                  
                  {parseFloat(event.total_contributions) > 0 && (
                    <div className="mt-2 text-sm text-blue-600">
                      <strong>Finance team will be notified to disburse {formatCurrency(event.total_contributions)}</strong>
                    </div>
                  )}
                </div>
                <button
                  onClick={handleCloseEvent}
                  disabled={closing}
                  className="ml-4 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {closing ? 'Closing...' : 'Close Event'}
                </button>
              </div>
            </div>
          )}

          {/* Cancel Event */}
          {canCancelEvent() && (
            <div className="border border-red-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-gray-900">Cancel Event</h4>
                  <p className="text-sm text-gray-600 mt-1">
                    Permanently cancel this event. This action can only be performed if there are no contributions.
                  </p>
                  
                  {parseFloat(event.total_contributions) > 0 && (
                    <div className="mt-2 text-sm text-red-600">
                      <strong>Cannot cancel: Event has received contributions</strong>
                    </div>
                  )}
                </div>
                <button
                  onClick={handleCancelEvent}
                  disabled={cancelling || parseFloat(event.total_contributions) > 0}
                  className="ml-4 px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:opacity-50"
                >
                  {cancelling ? 'Cancelling...' : 'Cancel Event'}
                </button>
              </div>
            </div>
          )}

          {/* No Actions Available */}
          {!canCloseEvent() && !canCancelEvent() && (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No actions available</h3>
              <p className="mt-1 text-sm text-gray-500">
                You don't have permission to manage this event, or no actions are currently available.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Contributions */}
      {contributions.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Contributions</h3>
          </div>
          
          <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
            {contributions.slice(0, 10).map((contribution) => (
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
            
            {contributions.length > 10 && (
              <div className="px-6 py-4 text-center">
                <button
                  onClick={() => navigate(`/events/${eventId}`)}
                  className="text-sm text-blue-600 hover:text-blue-500"
                >
                  View all {contributions.length} contributions
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Help Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Event Management Guidelines</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• <strong>Close Event:</strong> Use when the event goal is reached or the event is complete</li>
          <li>• <strong>Cancel Event:</strong> Only available for events with no contributions</li>
          <li>• Finance team will be automatically notified when events are closed</li>
          <li>• All actions are permanent and cannot be undone</li>
          <li>• Contributors will be notified of event status changes</li>
          {user?.role === UserRole.FINANCE && (
            <li>• <strong>Finance Team:</strong> You can manage any event regardless of creator</li>
          )}
        </ul>
      </div>
    </div>
  )
}

export default EventClosure