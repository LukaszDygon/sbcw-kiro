/**
 * EventList component for displaying and filtering events
 * Shows active events with progress tracking and contribution interface
 */
import React, { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import AdvancedSearch, { SearchFilters } from './AdvancedSearch'
import EventsService from '../services/events'

import { EventAccount, EventStatus } from '../types'

interface EventFilters extends SearchFilters {
  status?: string
  creator?: string
}

interface PaginationInfo {
  page: number
  per_page: number
  total: number
  pages: number
  offset: number
  has_more: boolean
}

const EventList: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [events, setEvents] = useState<EventAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<EventFilters>({})
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    per_page: 12,
    total: 0,
    pages: 0,
    offset: 0,
    has_more: false
  })


  // Load events
  const loadEvents = useCallback(async (page = 1) => {
    try {
      setLoading(true)
      setError(null)

      const limit = pagination.per_page
      const offset = (page - 1) * pagination.per_page

      let response
      if (filters.searchTerm) {
        response = await EventsService.searchEvents(filters.searchTerm, filters.status as any, limit, offset)
      } else {
        response = await EventsService.getActiveEvents(limit, offset)
      }

      // Transform response to match expected format
      const total = response.pagination?.total || response.events.length
      const transformedResponse = {
        events: response.events,
        pagination: {
          page,
          per_page: limit,
          total,
          pages: Math.ceil(total / limit),
          offset: response.pagination?.offset || 0,
          has_more: response.pagination?.has_more || false
        }
      }
      
      setEvents(transformedResponse.events)
      setPagination(transformedResponse.pagination)
    } catch (error: any) {
      console.error('Failed to load events:', error)
      setError(error.message || 'Failed to load events')
    } finally {
      setLoading(false)
    }
  }, [filters, pagination.per_page])

  // Load events when filters change
  useEffect(() => {
    if (user) {
      loadEvents(1)
    }
  }, [user, loadEvents])

  const handleFiltersChange = (newFilters: SearchFilters) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters
    }))
  }

  const handleSearch = () => {
    loadEvents(1)
  }

  const clearFilters = () => {
    setFilters({})
  }

  const handleContribute = (eventId: string) => {
    navigate(`/events/${eventId}/contribute`)
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
      month: 'short',
      day: 'numeric'
    })
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

  const isExpired = (deadline?: string) => {
    if (!deadline) return false
    return new Date(deadline) < new Date()
  }

  const getDaysUntilDeadline = (deadline?: string) => {
    if (!deadline) return null
    const days = Math.ceil((new Date(deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
    return days
  }

  if (loading && events.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" message="Loading events..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Events</h1>
          <p className="text-gray-600">
            {pagination.total > 0 
              ? `${pagination.total} event${pagination.total !== 1 ? 's' : ''} available`
              : 'No events found'
            }
          </p>
        </div>
        <Link
          to="/events/create"
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
        >
          <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Create Event
        </Link>
      </div>

      {/* Event Search */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              placeholder="Search events by name or description..."
              value={filters.searchTerm || ''}
              onChange={(e) => handleFiltersChange({ ...filters, searchTerm: e.target.value })}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <select
            value={filters.status || ''}
            onChange={(e) => handleFiltersChange({ ...filters, status: e.target.value })}
            className="border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">All Statuses</option>
            <option value={EventStatus.ACTIVE}>Active</option>
            <option value={EventStatus.CLOSED}>Closed</option>
            <option value={EventStatus.CANCELLED}>Cancelled</option>
          </select>
          
          <button
            onClick={handleSearch}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            Search
          </button>
          
          {(filters.searchTerm || filters.status) && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Events</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
              <div className="mt-4">
                <button
                  onClick={() => loadEvents(pagination.page)}
                  className="bg-red-100 px-2 py-1 text-sm text-red-800 rounded hover:bg-red-200"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Events Grid */}
      {events.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((event) => (
              <div key={event.id} className="bg-white shadow rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                {/* Event Header */}
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <Link
                        to={`/events/${event.id}`}
                        className="text-lg font-semibold text-gray-900 hover:text-blue-600"
                      >
                        {event.name}
                      </Link>
                      <p className="text-sm text-gray-500 mt-1">
                        by {event.creator_name}
                      </p>
                    </div>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(event.status)}`}>
                      {event.status.toLowerCase()}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mt-3 line-clamp-2">
                    {event.description}
                  </p>
                </div>

                {/* Progress Section */}
                <div className="px-6 pb-4">
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
                          className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(EventsService.getProgressPercentage(event) || 0)}`}
                          style={{ width: `${Math.min(EventsService.getProgressPercentage(event) || 0, 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>{EventsService.getProgressPercentage(event)?.toFixed(1) || 0}% complete</span>
                        <span>Contributors</span>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Raised</span>
                        <span className="font-medium text-green-600">
                          {formatCurrency(event.total_contributions)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        View details for contribution information
                      </div>
                    </div>
                  )}
                </div>

                {/* Event Details */}
                <div className="px-6 pb-4 space-y-2">
                  <div className="flex items-center text-xs text-gray-500">
                    <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0h6a2 2 0 012 2v10a2 2 0 01-2 2H8a2 2 0 01-2-2V9a2 2 0 012-2z" />
                    </svg>
                    Created {formatDate(event.created_at)}
                  </div>
                  
                  {event.deadline && (
                    <div className={`flex items-center text-xs ${
                      isExpired(event.deadline) ? 'text-red-500' : 
                      getDaysUntilDeadline(event.deadline)! <= 7 ? 'text-yellow-600' : 'text-gray-500'
                    }`}>
                      <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {isExpired(event.deadline) ? (
                        'Expired'
                      ) : (
                        `${getDaysUntilDeadline(event.deadline)} day${getDaysUntilDeadline(event.deadline) !== 1 ? 's' : ''} left`
                      )}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="px-6 pb-6 flex space-x-3">
                  <Link
                    to={`/events/${event.id}`}
                    className="flex-1 text-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    View Details
                  </Link>
                  {event.status === EventStatus.ACTIVE && !isExpired(event.deadline) && (
                    <button
                      onClick={() => handleContribute(event.id)}
                      className="flex-1 px-3 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                    >
                      Contribute
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-between">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => loadEvents(pagination.page - 1)}
                  disabled={pagination.page <= 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => loadEvents(pagination.page + 1)}
                  disabled={pagination.page >= pagination.pages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing{' '}
                    <span className="font-medium">{((pagination.page - 1) * pagination.per_page) + 1}</span>
                    {' '}to{' '}
                    <span className="font-medium">
                      {Math.min(pagination.page * pagination.per_page, pagination.total)}
                    </span>
                    {' '}of{' '}
                    <span className="font-medium">{pagination.total}</span>
                    {' '}events
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => loadEvents(pagination.page - 1)}
                      disabled={pagination.page <= 1}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">Previous</span>
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                      </svg>
                    </button>
                    
                    {/* Page numbers */}
                    {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                      const pageNum = Math.max(1, Math.min(pagination.pages - 4, pagination.page - 2)) + i
                      return (
                        <button
                          key={pageNum}
                          onClick={() => loadEvents(pageNum)}
                          className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                            pageNum === pagination.page
                              ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                              : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                          }`}
                        >
                          {pageNum}
                        </button>
                      )
                    })}

                    <button
                      onClick={() => loadEvents(pagination.page + 1)}
                      disabled={pagination.page >= pagination.pages}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">Next</span>
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No events found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {Object.keys(filters).length > 0 
              ? 'Try adjusting your filters to see more events.'
              : 'Get started by creating your first event.'
            }
          </p>
          {Object.keys(filters).length === 0 && (
            <div className="mt-6">
              <Link
                to="/events/create"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Create Event
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EventList