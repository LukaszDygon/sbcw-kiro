/**
 * Events service for SoftBankCashWire frontend
 */
import apiClient, { handleApiError } from './api'
import { EventAccount, EventStatus, Transaction } from '../types'

export interface CreateEventRequest {
  name: string
  description: string
  target_amount?: string
  deadline?: string
}

export interface CreateEventResult {
  success: boolean
  event: EventAccount
}

export interface ContributeToEventRequest {
  amount: string
  note?: string
}

export interface ContributeToEventResult {
  success: boolean
  contribution: Transaction
  contributor_balance: string
  event: EventAccount
  warnings: Array<{
    code: string
    message: string
  }>
}

export interface EventActionResult {
  success: boolean
  event: EventAccount
  message: string
}

export interface EventList {
  events: EventAccount[]
  pagination?: {
    total: number
    limit: number
    offset: number
    has_more: boolean
  }
  search_term?: string
}

export interface EventContribution {
  id: string
  contributor_id: string
  contributor_name: string
  amount: string
  note?: string
  created_at: string
}

export interface EventContributionsResult {
  event_id: string
  event_name: string
  contributions: EventContribution[]
  total_contributions: string
  contributor_count: number
}

export interface EventStatistics {
  period_days: number
  events_created: number
  active_events: number
  closed_events: number
  cancelled_events: number
  contributions: {
    total_count: number
    total_amount: string
    average_amount: string
    unique_contributors: number
  }
  popular_events: Array<{
    event_id: string
    event_name: string
    contribution_count: number
    total_contributions: string
  }>
}

export interface EventValidationResult {
  valid: boolean
  errors: Array<{
    code: string
    message: string
  }>
  warnings: Array<{
    code: string
    message: string
  }>
}

class EventsService {
  /**
   * Create a new event account
   */
  static async createEvent(request: CreateEventRequest): Promise<CreateEventResult> {
    try {
      const response = await apiClient.post('/events/create', request)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Contribute to an event account
   */
  static async contributeToEvent(eventId: string, request: ContributeToEventRequest): Promise<ContributeToEventResult> {
    try {
      const response = await apiClient.post(`/events/${eventId}/contribute`, request)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Close an event account
   */
  static async closeEvent(eventId: string): Promise<EventActionResult> {
    try {
      const response = await apiClient.post(`/events/${eventId}/close`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Cancel an event account
   */
  static async cancelEvent(eventId: string): Promise<EventActionResult> {
    try {
      const response = await apiClient.post(`/events/${eventId}/cancel`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get event details by ID
   */
  static async getEvent(eventId: string, includeContributions: boolean = false): Promise<{ event: EventAccount }> {
    try {
      const params = includeContributions ? '?include_contributions=true' : ''
      const response = await apiClient.get(`/events/${eventId}${params}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get contributions for a specific event
   */
  static async getEventContributions(eventId: string): Promise<EventContributionsResult> {
    try {
      const response = await apiClient.get(`/events/${eventId}/contributions`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get active events
   */
  static async getActiveEvents(limit: number = 50, offset: number = 0): Promise<EventList> {
    try {
      const params = new URLSearchParams()
      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      const response = await apiClient.get(`/events/active?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get events created by current user
   */
  static async getMyEvents(
    status?: EventStatus,
    limit: number = 50,
    offset: number = 0
  ): Promise<EventList> {
    try {
      const params = new URLSearchParams()
      if (status) params.append('status', status)
      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      const response = await apiClient.get(`/events/my-events?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get contributions made by current user
   */
  static async getMyContributions(limit: number = 50, offset: number = 0): Promise<{
    contributions: Transaction[]
    pagination: {
      total: number
      limit: number
      offset: number
      has_more: boolean
    }
  }> {
    try {
      const params = new URLSearchParams()
      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      const response = await apiClient.get(`/events/my-contributions?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Search events
   */
  static async searchEvents(
    searchTerm: string,
    status?: EventStatus,
    limit: number = 50,
    offset: number = 0
  ): Promise<EventList> {
    try {
      const params = new URLSearchParams()
      params.append('q', searchTerm)
      if (status) params.append('status', status)
      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      const response = await apiClient.get(`/events/search?${params.toString()}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Get event statistics
   */
  static async getEventStatistics(days: number = 30): Promise<EventStatistics> {
    try {
      const response = await apiClient.get(`/events/statistics?days=${days}`)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Validate event creation
   */
  static async validateEventCreation(eventData: CreateEventRequest): Promise<EventValidationResult> {
    try {
      const response = await apiClient.post('/events/validate', eventData)
      return response.data
    } catch (error) {
      throw handleApiError(error)
    }
  }

  /**
   * Format currency amount for display
   */
  static formatCurrency(amount: string, currency: string = 'GBP'): string {
    const numAmount = parseFloat(amount)

    if (currency === 'GBP') {
      return new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: 'GBP',
      }).format(numAmount)
    }

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(numAmount)
  }

  /**
   * Get event status color for UI
   */
  static getEventStatusColor(status: EventStatus): 'success' | 'warning' | 'error' | 'info' {
    switch (status) {
      case EventStatus.ACTIVE:
        return 'success'
      case EventStatus.CLOSED:
        return 'info'
      case EventStatus.CANCELLED:
        return 'error'
      default:
        return 'warning'
    }
  }

  /**
   * Get event status display name
   */
  static getEventStatusDisplayName(status: EventStatus): string {
    switch (status) {
      case EventStatus.ACTIVE:
        return 'Active'
      case EventStatus.CLOSED:
        return 'Closed'
      case EventStatus.CANCELLED:
        return 'Cancelled'
      default:
        return 'Unknown'
    }
  }

  /**
   * Check if event has deadline passed
   */
  static isEventDeadlinePassed(event: EventAccount): boolean {
    if (!event.deadline) return false
    return new Date(event.deadline) < new Date()
  }

  /**
   * Check if event deadline is approaching
   */
  static isEventDeadlineApproaching(event: EventAccount, hoursThreshold: number = 24): boolean {
    if (!event.deadline || event.status !== EventStatus.ACTIVE) return false

    const deadlineTime = new Date(event.deadline).getTime()
    const now = new Date().getTime()
    const hoursUntilDeadline = (deadlineTime - now) / (1000 * 60 * 60)

    return hoursUntilDeadline <= hoursThreshold && hoursUntilDeadline > 0
  }

  /**
   * Get time until deadline
   */
  static getTimeUntilDeadline(event: EventAccount): {
    passed: boolean
    days: number
    hours: number
    minutes: number
  } {
    if (!event.deadline) {
      return { passed: false, days: 0, hours: 0, minutes: 0 }
    }

    const deadlineTime = new Date(event.deadline).getTime()
    const now = new Date().getTime()
    const timeDiff = deadlineTime - now

    if (timeDiff <= 0) {
      return { passed: true, days: 0, hours: 0, minutes: 0 }
    }

    const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24))
    const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60))

    return { passed: false, days, hours, minutes }
  }

  /**
   * Format time until deadline for display
   */
  static formatTimeUntilDeadline(event: EventAccount): string {
    if (!event.deadline) {
      return 'No deadline'
    }

    const timeInfo = this.getTimeUntilDeadline(event)

    if (timeInfo.passed) {
      return 'Deadline passed'
    }

    if (timeInfo.days > 0) {
      return `${timeInfo.days} day${timeInfo.days > 1 ? 's' : ''} remaining`
    }

    if (timeInfo.hours > 0) {
      return `${timeInfo.hours} hour${timeInfo.hours > 1 ? 's' : ''} remaining`
    }

    if (timeInfo.minutes > 0) {
      return `${timeInfo.minutes} minute${timeInfo.minutes > 1 ? 's' : ''} remaining`
    }

    return 'Deadline soon'
  }

  /**
   * Calculate progress percentage towards target
   */
  static getProgressPercentage(event: EventAccount): number | null {
    if (!event.target_amount) return null

    const target = parseFloat(event.target_amount)
    const current = parseFloat(event.total_contributions)

    if (target <= 0) return null

    return Math.min((current / target) * 100, 100)
  }

  /**
   * Get remaining amount to reach target
   */
  static getRemainingAmount(event: EventAccount): string | null {
    if (!event.target_amount) return null

    const target = parseFloat(event.target_amount)
    const current = parseFloat(event.total_contributions)

    const remaining = Math.max(target - current, 0)
    return remaining.toFixed(2)
  }

  /**
   * Check if event target is reached
   */
  static isTargetReached(event: EventAccount): boolean {
    if (!event.target_amount) return false

    const target = parseFloat(event.target_amount)
    const current = parseFloat(event.total_contributions)

    return current >= target
  }

  /**
   * Validate event name
   */
  static validateEventName(name: string): { valid: boolean; error?: string } {
    if (!name || name.trim() === '') {
      return { valid: false, error: 'Event name is required' }
    }

    if (name.length > 255) {
      return { valid: false, error: 'Event name cannot exceed 255 characters' }
    }

    return { valid: true }
  }

  /**
   * Validate event description
   */
  static validateEventDescription(description: string): { valid: boolean; error?: string } {
    if (!description || description.trim() === '') {
      return { valid: false, error: 'Event description is required' }
    }

    if (description.length > 1000) {
      return { valid: false, error: 'Event description cannot exceed 1000 characters' }
    }

    return { valid: true }
  }

  /**
   * Validate target amount
   */
  static validateTargetAmount(amount?: string): { valid: boolean; error?: string } {
    if (!amount || amount.trim() === '') {
      return { valid: true } // Target amount is optional
    }

    const numAmount = parseFloat(amount)

    if (isNaN(numAmount)) {
      return { valid: false, error: 'Target amount must be a valid number' }
    }

    if (numAmount <= 0) {
      return { valid: false, error: 'Target amount must be positive' }
    }

    if (numAmount > 100000) {
      return { valid: false, error: 'Target amount cannot exceed £100,000' }
    }

    // Check for reasonable decimal places
    const decimalPlaces = (amount.split('.')[1] || '').length
    if (decimalPlaces > 2) {
      return { valid: false, error: 'Target amount cannot have more than 2 decimal places' }
    }

    return { valid: true }
  }

  /**
   * Validate deadline
   */
  static validateDeadline(deadline?: string): { valid: boolean; error?: string } {
    if (!deadline || deadline.trim() === '') {
      return { valid: true } // Deadline is optional
    }

    try {
      const deadlineDate = new Date(deadline)

      if (isNaN(deadlineDate.getTime())) {
        return { valid: false, error: 'Deadline must be a valid date' }
      }

      if (deadlineDate <= new Date()) {
        return { valid: false, error: 'Deadline must be in the future' }
      }

      // Check if deadline is too far in the future (e.g., more than 2 years)
      const twoYearsFromNow = new Date()
      twoYearsFromNow.setFullYear(twoYearsFromNow.getFullYear() + 2)

      if (deadlineDate > twoYearsFromNow) {
        return { valid: false, error: 'Deadline cannot be more than 2 years in the future' }
      }

      return { valid: true }
    } catch {
      return { valid: false, error: 'Deadline must be a valid date' }
    }
  }

  /**
   * Validate contribution amount
   */
  static validateContributionAmount(amount: string): { valid: boolean; error?: string } {
    if (!amount || amount.trim() === '') {
      return { valid: false, error: 'Contribution amount is required' }
    }

    const numAmount = parseFloat(amount)

    if (isNaN(numAmount)) {
      return { valid: false, error: 'Amount must be a valid number' }
    }

    if (numAmount <= 0) {
      return { valid: false, error: 'Amount must be positive' }
    }

    if (numAmount > 10000) {
      return { valid: false, error: 'Amount cannot exceed £10,000' }
    }

    // Check for reasonable decimal places
    const decimalPlaces = (amount.split('.')[1] || '').length
    if (decimalPlaces > 2) {
      return { valid: false, error: 'Amount cannot have more than 2 decimal places' }
    }

    return { valid: true }
  }

  /**
   * Validate contribution note
   */
  static validateContributionNote(note?: string): { valid: boolean; error?: string } {
    if (!note) {
      return { valid: true } // Note is optional
    }

    if (note.length > 500) {
      return { valid: false, error: 'Note cannot exceed 500 characters' }
    }

    return { valid: true }
  }

  /**
   * Sort events by various criteria
   */
  static sortEvents(
    events: EventAccount[],
    sortBy: 'date' | 'name' | 'target' | 'contributions' | 'deadline',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): EventAccount[] {
    const sorted = [...events].sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'date':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
          break
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'target':
          const aTarget = parseFloat(a.target_amount || '0')
          const bTarget = parseFloat(b.target_amount || '0')
          comparison = aTarget - bTarget
          break
        case 'contributions':
          comparison = parseFloat(a.total_contributions) - parseFloat(b.total_contributions)
          break
        case 'deadline':
          const aDeadline = a.deadline ? new Date(a.deadline).getTime() : 0
          const bDeadline = b.deadline ? new Date(b.deadline).getTime() : 0
          comparison = aDeadline - bDeadline
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return sorted
  }

  /**
   * Filter events by text search
   */
  static searchEventsLocal(events: EventAccount[], searchText: string): EventAccount[] {
    if (!searchText.trim()) {
      return events
    }

    const searchLower = searchText.toLowerCase()

    return events.filter(event => {
      return (
        event.name.toLowerCase().includes(searchLower) ||
        event.description.toLowerCase().includes(searchLower) ||
        event.creator_name?.toLowerCase().includes(searchLower)
      )
    })
  }

  /**
   * Group events by status
   */
  static groupEventsByStatus(events: EventAccount[]): Record<EventStatus, EventAccount[]> {
    const grouped: Record<EventStatus, EventAccount[]> = {
      [EventStatus.ACTIVE]: [],
      [EventStatus.CLOSED]: [],
      [EventStatus.CANCELLED]: [],
    }

    events.forEach(event => {
      grouped[event.status].push(event)
    })

    return grouped
  }

  /**
   * Check if user can contribute to event
   */
  static canContributeToEvent(event: EventAccount, currentUserId: string): boolean {
    return (
      event.status === EventStatus.ACTIVE &&
      !this.isEventDeadlinePassed(event)
    )
  }

  /**
   * Check if user can close event
   */
  static canCloseEvent(event: EventAccount, currentUserId: string): boolean {
    return (
      event.status === EventStatus.ACTIVE &&
      event.creator_id === currentUserId
    )
  }

  /**
   * Check if user can cancel event
   */
  static canCancelEvent(event: EventAccount, currentUserId: string): boolean {
    return (
      event.status === EventStatus.ACTIVE &&
      event.creator_id === currentUserId &&
      parseFloat(event.total_contributions) === 0
    )
  }
}

export const eventsService = EventsService
export default EventsService