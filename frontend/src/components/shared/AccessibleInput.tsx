/**
 * Accessible Input component
 * WCAG 2.1 AA compliant input with proper labeling and error handling
 */
import React, { forwardRef, InputHTMLAttributes } from 'react'

interface AccessibleInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  helperText?: string
  required?: boolean
  hideLabel?: boolean
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
}

const AccessibleInput = forwardRef<HTMLInputElement, AccessibleInputProps>(({
  label,
  error,
  helperText,
  required = false,
  hideLabel = false,
  icon,
  iconPosition = 'left',
  className = '',
  id,
  ...props
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`
  const errorId = error ? `${inputId}-error` : undefined
  const helperId = helperText ? `${inputId}-helper` : undefined
  const describedBy = [errorId, helperId].filter(Boolean).join(' ') || undefined

  const inputClasses = `
    input block w-full px-3 py-2 border rounded-md shadow-sm
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
    disabled:bg-gray-100 disabled:cursor-not-allowed
    ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
    ${icon && iconPosition === 'left' ? 'pl-10' : ''}
    ${icon && iconPosition === 'right' ? 'pr-10' : ''}
    ${className}
  `.trim()

  return (
    <div className="space-y-1">
      {/* Label */}
      <label 
        htmlFor={inputId}
        className={`block text-sm font-medium text-gray-700 ${hideLabel ? 'sr-only' : ''}`}
      >
        {label}
        {required && (
          <span className="text-red-500 ml-1" aria-label="required">
            *
          </span>
        )}
      </label>

      {/* Input container */}
      <div className="relative">
        {/* Left icon */}
        {icon && iconPosition === 'left' && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400" aria-hidden="true">
              {icon}
            </span>
          </div>
        )}

        {/* Input */}
        <input
          ref={ref}
          id={inputId}
          className={inputClasses}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={describedBy}
          aria-required={required}
          {...props}
        />

        {/* Right icon */}
        {icon && iconPosition === 'right' && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <span className="text-gray-400" aria-hidden="true">
              {icon}
            </span>
          </div>
        )}

        {/* Error icon */}
        {error && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
            <svg 
              className="h-5 w-5 text-red-500" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" 
              />
            </svg>
          </div>
        )}
      </div>

      {/* Helper text */}
      {helperText && !error && (
        <p 
          id={helperId}
          className="text-sm text-gray-500"
        >
          {helperText}
        </p>
      )}

      {/* Error message */}
      {error && (
        <p 
          id={errorId}
          className="text-sm text-red-600"
          role="alert"
          aria-live="polite"
        >
          {error}
        </p>
      )}
    </div>
  )
})

AccessibleInput.displayName = 'AccessibleInput'

export default AccessibleInput