/**
 * Login page component with Microsoft SSO integration
 * Handles authentication flow and error states
 */
import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import AuthService from '../services/auth'
import LoadingSpinner from './shared/LoadingSpinner'

interface LoginPageProps {
  onLoginSuccess?: () => void
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loginUrl, setLoginUrl] = useState<string | null>(null)

  const redirectUrl = searchParams.get('redirect') || '/dashboard'
  const reason = searchParams.get('reason')

  useEffect(() => {
    // Check if user is already authenticated
    if (AuthService.isAuthenticated()) {
      navigate(redirectUrl, { replace: true })
      return
    }

    // Get login URL from backend
    const getLoginUrl = async () => {
      try {
        const response = await AuthService.getLoginUrl(window.location.origin + '/auth/callback')
        setLoginUrl(response.login_url)
      } catch (error) {
        console.error('Failed to get login URL:', error)
        setError('Failed to initialize login. Please try again.')
      }
    }

    getLoginUrl()
  }, [navigate, redirectUrl])

  const handleMicrosoftLogin = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const authResponse = await AuthService.loginWithMicrosoft()
      
      if (authResponse.user) {
        onLoginSuccess?.()
        navigate(redirectUrl, { replace: true })
      }
    } catch (error: any) {
      console.error('Login failed:', error)
      setError(error.message || 'Login failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleBackendLogin = () => {
    if (loginUrl) {
      window.location.href = loginUrl
    } else {
      setError('Login URL not available. Please refresh the page.')
    }
  }

  const getErrorMessage = () => {
    if (reason === 'session_expired') {
      return 'Your session has expired. Please log in again.'
    }
    if (reason === 'unauthorized') {
      return 'You need to log in to access this page.'
    }
    return error
  }

  const errorMessage = getErrorMessage()

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
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to SoftBankCashWire
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Use your Microsoft account to access the internal banking system
          </p>
        </div>

        <div className="mt-8 space-y-6">
          {errorMessage && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    Authentication Error
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    {errorMessage}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {/* Microsoft SSO Login Button */}
            <button
              onClick={handleMicrosoftLogin}
              disabled={isLoading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <LoadingSpinner size="small" className="mr-2" />
              ) : (
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M23.5 12.3c0-.8-.1-1.6-.2-2.4H12v4.5h6.4c-.3 1.5-1.1 2.8-2.4 3.7v3.1h3.9c2.3-2.1 3.6-5.2 3.6-8.9z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 24c3.2 0 6-1.1 8-2.9l-3.9-3.1c-1.1.7-2.5 1.2-4.1 1.2-3.2 0-5.9-2.1-6.9-5h-4v3.2C3.2 21.1 7.3 24 12 24z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.1 14.2c-.2-.7-.4-1.4-.4-2.2s.1-1.5.4-2.2V6.6h-4C.4 8.9 0 10.4 0 12s.4 3.1 1.1 4.4l4-3.2z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 4.8c1.8 0 3.4.6 4.6 1.8l3.5-3.5C18 1.1 15.2 0 12 0 7.3 0 3.2 2.9 1.1 7.2l4 3.1c1-2.9 3.7-5 6.9-5z"
                  />
                </svg>
              )}
              {isLoading ? 'Signing in...' : 'Sign in with Microsoft'}
            </button>

            {/* Alternative Backend Login */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-50 text-gray-500">Or</span>
              </div>
            </div>

            <button
              onClick={handleBackendLogin}
              disabled={isLoading || !loginUrl}
              className="group relative w-full flex justify-center py-3 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {!loginUrl ? (
                <LoadingSpinner size="small" className="mr-2" />
              ) : (
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              )}
              {!loginUrl ? 'Loading...' : 'Sign in via Browser'}
            </button>
          </div>

          <div className="text-center">
            <p className="text-xs text-gray-500">
              By signing in, you agree to our terms of service and privacy policy.
              This system is for authorized SoftBank employees only.
            </p>
          </div>
        </div>

        {/* Session Information */}
        {reason && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-yellow-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  {reason === 'session_expired' && 'Your session has expired for security reasons.'}
                  {reason === 'unauthorized' && 'Please log in to access the requested page.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Development Info */}
        {import.meta.env.DEV && (
          <div className="mt-4 p-3 bg-gray-100 border border-gray-200 rounded-md">
            <p className="text-xs text-gray-600">
              <strong>Development Mode:</strong> Microsoft Client ID: {import.meta.env.VITE_MICROSOFT_CLIENT_ID || 'Not configured'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default LoginPage