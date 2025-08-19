/**
 * OAuth callback handler component
 * Processes Microsoft OAuth callback and completes authentication
 */
import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import AuthService from '../services/auth'
import LoadingSpinner from './shared/LoadingSpinner'

const AuthCallback: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get parameters from URL
        const code = searchParams.get('code')
        const state = searchParams.get('state')
        const error = searchParams.get('error')
        const errorDescription = searchParams.get('error_description')

        // Check for OAuth errors
        if (error) {
          throw new Error(errorDescription || `OAuth error: ${error}`)
        }

        // Check for required parameters
        if (!code) {
          throw new Error('Authorization code not found in callback URL')
        }

        // Get redirect URI from session storage or use default
        const redirectUri = sessionStorage.getItem('oauth_redirect_uri') || 
                           window.location.origin + '/auth/callback'

        // Handle the callback
        const authResponse = await AuthService.handleCallback(code, redirectUri, state || undefined)

        if (authResponse.user) {
          setStatus('success')
          
          // Get the original redirect URL
          const originalRedirect = sessionStorage.getItem('pre_auth_redirect') || '/dashboard'
          sessionStorage.removeItem('pre_auth_redirect')
          sessionStorage.removeItem('oauth_redirect_uri')

          // Small delay to show success state
          setTimeout(() => {
            navigate(originalRedirect, { replace: true })
          }, 1500)
        } else {
          throw new Error('Authentication succeeded but no user data received')
        }
      } catch (error: any) {
        console.error('OAuth callback failed:', error)
        setError(error.message || 'Authentication failed')
        setStatus('error')

        // Redirect to login after showing error
        setTimeout(() => {
          navigate('/login?reason=callback_failed', { replace: true })
        }, 3000)
      }
    }

    handleCallback()
  }, [navigate, searchParams])

  const renderContent = () => {
    switch (status) {
      case 'processing':
        return (
          <div className="text-center">
            <LoadingSpinner size="large" className="mb-4" />
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Completing Sign In
            </h2>
            <p className="text-gray-600">
              Please wait while we complete your authentication...
            </p>
            <div className="mt-4 text-sm text-gray-500">
              This should only take a few seconds.
            </div>
          </div>
        )

      case 'success':
        return (
          <div className="text-center">
            <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-green-100 mb-4">
              <svg
                className="h-10 w-10 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Sign In Successful
            </h2>
            <p className="text-gray-600">
              Welcome to SoftBankCashWire! Redirecting you now...
            </p>
          </div>
        )

      case 'error':
        return (
          <div className="text-center">
            <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-red-100 mb-4">
              <svg
                className="h-10 w-10 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Sign In Failed
            </h2>
            <p className="text-gray-600 mb-4">
              {error || 'An unexpected error occurred during authentication.'}
            </p>
            <div className="space-y-2">
              <button
                onClick={() => navigate('/login', { replace: true })}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Try Again
              </button>
              <div className="text-sm text-gray-500">
                Redirecting to login page in a few seconds...
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
            <svg
              className="h-8 w-8 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
        </div>

        {renderContent()}

        {/* Debug information in development */}
        {import.meta.env.DEV && (
          <div className="mt-8 p-4 bg-gray-100 border border-gray-200 rounded-md">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Debug Info</h3>
            <div className="text-xs text-gray-600 space-y-1">
              <div>Code: {searchParams.get('code') ? 'Present' : 'Missing'}</div>
              <div>State: {searchParams.get('state') || 'Not provided'}</div>
              <div>Error: {searchParams.get('error') || 'None'}</div>
              <div>Status: {status}</div>
              {error && <div>Error Message: {error}</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AuthCallback