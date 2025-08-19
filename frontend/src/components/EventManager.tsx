/**
 * EventManager component for event account creation
 * Handles event creation with validation and target amount settings
 */
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import EventsService from '../services/events'

interface EventForm {
  name: string
  description: string
  target_amount: string
  deadline: string
}

const EventManager: React.FC = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState<EventForm>({
    name: '',
    description: '',
    target_amount: '',
    deadline: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  const updateForm = (field: keyof EventForm, value: string) => {
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

    // Validate name
    if (!form.name.trim()) {
      errors.name = 'Event name is required'
      isValid = false
    } else if (form.name.length > 255) {
      errors.name = 'Event name cannot exceed 255 characters'
      isValid = false
    }

    // Validate description
    if (!form.description.trim()) {
      errors.description = 'Event description is required'
      isValid = false
    } else if (form.description.length > 1000) {
      errors.description = 'Event description cannot exceed 1000 characters'
      isValid = false
    }

    // Validate target amount (optional)
    if (form.target_amount) {
      const amount = parseFloat(form.target_amount)
      if (isNaN(amount) || amount <= 0) {
        errors.target_amount = 'Target amount must be greater than 0'
        isValid = false
      } else if (amount > 100000) {
        errors.target_amount = 'Target amount cannot exceed £100,000'
        isValid = false
      }
    }

    // Validate deadline (optional)
    if (form.deadline) {
      const deadline = new Date(form.deadline)
      const now = new Date()
      
      if (deadline <= now) {
        errors.deadline = 'Deadline must be in the future'
        isValid = false
      }
      
      // Check if deadline is too far in the future (1 year max)
      const oneYearFromNow = new Date()
      oneYearFromNow.setFullYear(oneYearFromNow.getFullYear() + 1)
      
      if (deadline > oneYearFromNow) {
        errors.deadline = 'Deadline cannot be more than 1 year in the future'
        isValid = false
      }
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

      const eventData: any = {
        name: form.name.trim(),
        description: form.description.trim()
      }

      if (form.target_amount) {
        eventData.target_amount = form.target_amount
      }

      if (form.deadline) {
        eventData.deadline = new Date(form.deadline).toISOString()
      }

      const response = await EventsService.createEvent(eventData)

      // Success - redirect to event detail
      navigate(`/events/${response.event.id}`, { 
        state: { message: 'Event created successfully!' }
      })
    } catch (error: any) {
      console.error('Failed to create event:', error)
      setError(error.message || 'Failed to create event')
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

  const getMinDate = () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow.toISOString().split('T')[0]
  }

  const getMaxDate = () => {
    const oneYearFromNow = new Date()
    oneYearFromNow.setFullYear(oneYearFromNow.getFullYear() + 1)
    return oneYearFromNow.toISOString().split('T')[0]
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create Event Account</h1>
        <p className="text-gray-600">
          Create a shared account for collecting contributions towards a common goal
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

      {/* Event Creation Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-6">Event Details</h3>

          <div className="space-y-6">
            {/* Event Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Event Name *
              </label>
              <input
                type="text"
                placeholder="e.g., Team Lunch, Office Party, Charity Drive"
                maxLength={255}
                value={form.name}
                onChange={(e) => updateForm('name', e.target.value)}
                className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  validationErrors.name ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {validationErrors.name && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Choose a clear, descriptive name for your event
              </p>
            </div>

            {/* Event Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description *
              </label>
              <textarea
                rows={4}
                placeholder="Describe what this event is for, when it will happen, and any other relevant details..."
                maxLength={1000}
                value={form.description}
                onChange={(e) => updateForm('description', e.target.value)}
                className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  validationErrors.description ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {validationErrors.description && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.description}</p>
              )}
              <div className="mt-1 flex justify-between text-sm text-gray-500">
                <span>Provide details to help colleagues understand and contribute</span>
                <span>{form.description.length}/1000</span>
              </div>
            </div>

            {/* Target Amount */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Amount (£) <span className="text-gray-500">(Optional)</span>
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="100000"
                  placeholder="0.00"
                  value={form.target_amount}
                  onChange={(e) => updateForm('target_amount', e.target.value)}
                  className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                    validationErrors.target_amount ? 'border-red-300' : 'border-gray-300'
                  }`}
                />
                {form.target_amount && (
                  <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                    <span className="text-gray-500 sm:text-sm">
                      {formatCurrency(form.target_amount)}
                    </span>
                  </div>
                )}
              </div>
              {validationErrors.target_amount && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.target_amount}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Set a fundraising goal (optional). Maximum: £100,000
              </p>
            </div>

            {/* Deadline */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Deadline <span className="text-gray-500">(Optional)</span>
              </label>
              <input
                type="date"
                min={getMinDate()}
                max={getMaxDate()}
                value={form.deadline}
                onChange={(e) => updateForm('deadline', e.target.value)}
                className={`block w-full border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  validationErrors.deadline ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {validationErrors.deadline && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.deadline}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Set a deadline for contributions (optional). Maximum: 1 year from now
              </p>
            </div>
          </div>
        </div>

        {/* Preview */}
        {form.name && form.description && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Event Preview</h4>
            <div className="text-sm text-blue-800 space-y-2">
              <div>
                <strong>Name:</strong> {form.name}
              </div>
              <div>
                <strong>Description:</strong> {form.description}
              </div>
              {form.target_amount && (
                <div>
                  <strong>Target:</strong> {formatCurrency(form.target_amount)}
                </div>
              )}
              {form.deadline && (
                <div>
                  <strong>Deadline:</strong> {new Date(form.deadline).toLocaleDateString('en-GB', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </div>
              )}
              <div>
                <strong>Created by:</strong> {user?.name}
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/events')}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading || !form.name.trim() || !form.description.trim()}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <LoadingSpinner size="small" className="mr-2" />
                Creating Event...
              </>
            ) : (
              'Create Event'
            )}
          </button>
        </div>
      </form>

      {/* Help Section */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">How Event Accounts Work</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Event accounts collect contributions from multiple people towards a common goal</li>
          <li>• Anyone can contribute to your event once it's created</li>
          <li>• You can set an optional target amount and deadline</li>
          <li>• Track progress and see who has contributed</li>
          <li>• Close the event when the goal is reached or the event is complete</li>
          <li>• Only you or finance team members can close the event account</li>
        </ul>
      </div>
    </div>
  )
}

export default EventManager