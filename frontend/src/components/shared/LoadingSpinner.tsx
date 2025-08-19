/**
 * Accessible Loading spinner component
 * WCAG 2.1 AA compliant with proper ARIA attributes and screen reader support
 */
import React from 'react'
import { useAccessibility } from '../../contexts/AccessibilityContext'

interface LoadingSpinnerProps {
  size?: 'small' | 'sm' | 'md' | 'lg' | 'large'
  className?: string
  message?: string
  'aria-label'?: string
  'aria-describedby'?: string
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className = '',
  message,
  'aria-label': ariaLabel,
  'aria-describedby': ariaDescribedBy,
}) => {
  const { preferences } = useAccessibility()

  const sizeClasses = {
    small: 'w-4 h-4',
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    large: 'w-12 h-12',
  }

  const spinnerClass = preferences.reduceMotion 
    ? 'spinner border-2 border-gray-200 border-t-blue-600 rounded-full'
    : 'spinner border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin'

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div
        className={`${sizeClasses[size]} ${spinnerClass}`}
        role="status"
        aria-label={ariaLabel || (message ? `Loading: ${message}` : 'Loading')}
        aria-describedby={ariaDescribedBy}
        aria-live="polite"
      >
        <span className="sr-only">
          {message || 'Loading, please wait...'}
        </span>
      </div>
      {message && (
        <p 
          className="mt-2 text-sm text-gray-600"
          id={ariaDescribedBy}
          aria-live="polite"
        >
          {message}
        </p>
      )}
    </div>
  )
}

export default LoadingSpinner