/**
 * Accessible Button component
 * WCAG 2.1 AA compliant button with proper focus management and keyboard support
 */
import React, { forwardRef, ButtonHTMLAttributes } from 'react'
import LoadingSpinner from './LoadingSpinner'

interface AccessibleButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'error' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  loadingText?: string
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
  fullWidth?: boolean
  'aria-describedby'?: string
}

const AccessibleButton = forwardRef<HTMLButtonElement, AccessibleButtonProps>(({
  variant = 'primary',
  size = 'md',
  loading = false,
  loadingText,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  children,
  className = '',
  disabled,
  'aria-describedby': ariaDescribedBy,
  ...props
}, ref) => {
  const baseClasses = 'btn inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
    error: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500 border border-gray-300',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm min-h-[36px]',
    md: 'px-4 py-2 text-sm min-h-[44px]',
    lg: 'px-6 py-3 text-base min-h-[52px]',
  }

  const widthClass = fullWidth ? 'w-full' : ''

  const isDisabled = disabled || loading

  const buttonContent = (
    <>
      {loading && (
        <LoadingSpinner 
          size="small" 
          className="mr-2" 
          aria-label={loadingText || 'Loading'}
        />
      )}
      {!loading && icon && iconPosition === 'left' && (
        <span className="mr-2" aria-hidden="true">
          {icon}
        </span>
      )}
      <span>
        {loading && loadingText ? loadingText : children}
      </span>
      {!loading && icon && iconPosition === 'right' && (
        <span className="ml-2" aria-hidden="true">
          {icon}
        </span>
      )}
    </>
  )

  return (
    <button
      ref={ref}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${widthClass} ${className}`}
      disabled={isDisabled}
      aria-disabled={isDisabled}
      aria-describedby={ariaDescribedBy}
      {...props}
    >
      {buttonContent}
    </button>
  )
})

AccessibleButton.displayName = 'AccessibleButton'

export default AccessibleButton