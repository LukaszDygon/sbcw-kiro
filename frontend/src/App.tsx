import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { AccessibilityProvider } from './contexts/AccessibilityContext'
import { useAuth } from './components/AuthGuard'

// Layout Components
import AccessibilitySettings from './components/AccessibilitySettings'
import NotificationBell from './components/NotificationBell'
import NotificationCenter from './components/NotificationCenter'
import NotificationManager from './components/NotificationManager'
import NotificationTestPanel from './components/NotificationTestPanel'
import ResponsiveNavigation from './components/shared/ResponsiveNavigation'

// Auth Components
import LoginPage from './components/LoginPage'
import AuthCallback from './components/AuthCallback'
import AuthGuard from './components/AuthGuard'

// Main Components
import Dashboard from './components/Dashboard'
import SendMoney from './components/SendMoney'
import RequestMoney from './components/RequestMoney'
import TransactionList from './components/TransactionList'
import EventManager from './components/EventManager'
import EventList from './components/EventList'
import EventDetails from './components/EventDetails'
import EventContribute from './components/EventContribute'
import EventClosure from './components/EventClosure'
import UserProfile from './components/UserProfile'
import Reports from './components/Reports'
import AdminPanel from './components/AdminPanel'

// Development mode check
const isDevelopment = import.meta.env.DEV || import.meta.env.VITE_DISABLE_AUTH === 'true'

// Navigation items
const getNavigationItems = (user: any) => [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v6H8V5z" />
      </svg>
    ),
    description: 'View your account overview and recent activity'
  },
  {
    label: 'Send Money',
    href: '/transactions/send',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
      </svg>
    ),
    description: 'Transfer money to other employees'
  },
  {
    label: 'Transactions',
    href: '/transactions/history',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
    description: 'View your transaction history'
  },
  {
    label: 'Events',
    href: '/events/active',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
    description: 'View and contribute to group events'
  },
  {
    label: 'Profile',
    href: '/profile',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
    description: 'Manage your account settings'
  },
  ...(user?.role === 'ADMIN' || user?.role === 'FINANCE' ? [{
    label: 'Reports',
    href: '/reports/admin',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    description: 'View financial reports and analytics'
  }] : []),
  ...(user?.role === 'ADMIN' ? [{
    label: 'Admin',
    href: '/admin',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    description: 'System administration and user management'
  }] : [])
]

// Layout wrapper component
const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isNotificationCenterOpen, setIsNotificationCenterOpen] = useState(false)
  const [isAccessibilitySettingsOpen, setIsAccessibilitySettingsOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleNotificationClick = (notification: any) => {
    // Handle notification click - navigate to relevant page
    console.log('Notification clicked:', notification)
    setIsNotificationCenterOpen(false)
    
    // Navigate based on notification type
    if (notification.action_url) {
      navigate(notification.action_url)
    }
  }

  const handleSkipToMain = () => {
    const mainContent = document.getElementById('main-content')
    if (mainContent) {
      mainContent.focus()
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Development Mode Banner */}
      {isDevelopment && (
        <div className="bg-yellow-500 text-black px-4 py-2 text-center text-sm font-medium">
          🚀 DEVELOPMENT MODE - Authentication Disabled - Using Real Admin User from Database
        </div>
      )}

      {/* Skip to main content link for screen readers */}
      <a 
        href="#main-content" 
        className="skip-link"
        onClick={handleSkipToMain}
      >
        Skip to main content
      </a>

      <header className="bg-white shadow-sm border-b border-gray-200" role="banner">
        <div className="container-responsive">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                SoftBankCashWire
              </h1>
            </div>
            
            <nav className="flex items-center space-x-4" role="navigation" aria-label="Main navigation">
              {user && (
                <>
                  <span className="text-sm text-gray-600">
                    Welcome, {user.name?.split(' ')[0]}
                  </span>
                  
                  {/* Accessibility Settings Button */}
                  <button
                    type="button"
                    onClick={() => setIsAccessibilitySettingsOpen(true)}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    aria-label="Open accessibility settings"
                    title="Accessibility Settings"
                  >
                    <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </button>

                  <NotificationBell
                    onClick={() => setIsNotificationCenterOpen(true)}
                    className="hover:bg-gray-100 rounded-full"
                  />

                  <button
                    onClick={handleLogout}
                    className="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    Logout
                  </button>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Navigation Menu */}
      {user && <ResponsiveNavigation items={getNavigationItems(user)} />}
      
      <main 
        id="main-content"
        className="container-responsive py-6"
        role="main"
        tabIndex={-1}
      >
        {children}
      </main>

      {/* Accessibility Settings Modal */}
      <AccessibilitySettings
        isOpen={isAccessibilitySettingsOpen}
        onClose={() => setIsAccessibilitySettingsOpen(false)}
      />

      {/* Notification Center */}
      <NotificationCenter
        isOpen={isNotificationCenterOpen}
        onClose={() => setIsNotificationCenterOpen(false)}
        onNotificationClick={handleNotificationClick}
      />

      {/* Real-time Notification Manager */}
      <NotificationManager />

      {/* Test Panel (development only) */}
      {import.meta.env.DEV && <NotificationTestPanel />}
    </div>
  )
}

// Unauthorized page component
const UnauthorizedPage: React.FC = () => (
  <div className="text-center py-12">
    <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-red-100 mb-4">
      <svg className="h-8 w-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    </div>
    <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
    <p className="text-gray-600 mb-4">You don't have permission to access this page.</p>
    <button
      onClick={() => window.history.back()}
      className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
    >
      Go Back
    </button>
  </div>
)

// Not found page component
const NotFoundPage: React.FC = () => (
  <div className="text-center py-12">
    <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-gray-100 mb-4">
      <svg className="h-8 w-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    </div>
    <h1 className="text-2xl font-bold text-gray-900 mb-2">Page Not Found</h1>
    <p className="text-gray-600 mb-4">The page you're looking for doesn't exist.</p>
    <button
      onClick={() => window.location.href = '/dashboard'}
      className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
    >
      Go to Dashboard
    </button>
  </div>
)

function App() {
  return (
    <AccessibilityProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          
          {/* Protected routes */}
          <Route path="/" element={
            <AuthGuard>
              <AppLayout>
                <Navigate to="/dashboard" replace />
              </AppLayout>
            </AuthGuard>
          } />
          
          <Route path="/dashboard" element={
            <AuthGuard>
              <AppLayout>
                <Dashboard />
              </AppLayout>
            </AuthGuard>
          } />

          {/* Transaction routes */}
          <Route path="/transactions/send" element={
            <AuthGuard>
              <AppLayout>
                <SendMoney />
              </AppLayout>
            </AuthGuard>
          } />
          
          <Route path="/transactions/history" element={
            <AuthGuard>
              <AppLayout>
                <TransactionList />
              </AppLayout>
            </AuthGuard>
          } />

          {/* Money request routes */}
          <Route path="/money-requests/create" element={
            <AuthGuard>
              <AppLayout>
                <RequestMoney />
              </AppLayout>
            </AuthGuard>
          } />

          {/* Event routes */}
          <Route path="/events/create" element={
            <AuthGuard>
              <AppLayout>
                <EventManager />
              </AppLayout>
            </AuthGuard>
          } />
          
          <Route path="/events/active" element={
            <AuthGuard>
              <AppLayout>
                <EventList />
              </AppLayout>
            </AuthGuard>
          } />
          
          <Route path="/events/:id" element={
            <AuthGuard>
              <AppLayout>
                <EventDetails />
              </AppLayout>
            </AuthGuard>
          } />
          
          <Route path="/events/:id/contribute" element={
            <AuthGuard>
              <AppLayout>
                <EventContribute />
              </AppLayout>
            </AuthGuard>
          } />
          
          <Route path="/events/:id/close" element={
            <AuthGuard requiredRole={['ADMIN', 'FINANCE']}>
              <AppLayout>
                <EventClosure />
              </AppLayout>
            </AuthGuard>
          } />

          {/* Profile route */}
          <Route path="/profile" element={
            <AuthGuard>
              <AppLayout>
                <UserProfile />
              </AppLayout>
            </AuthGuard>
          } />

          {/* Reports routes */}
          <Route path="/reports/personal" element={
            <AuthGuard>
              <AppLayout>
                <Reports currentUser={null} />
              </AppLayout>
            </AuthGuard>
          } />
          
          <Route path="/reports/admin" element={
            <AuthGuard requiredRole={['ADMIN', 'FINANCE']}>
              <AppLayout>
                <Reports currentUser={null} />
              </AppLayout>
            </AuthGuard>
          } />

          {/* Admin routes */}
          <Route path="/admin" element={
            <AuthGuard requiredRole="ADMIN">
              <AppLayout>
                <AdminPanel currentUser={null} />
              </AppLayout>
            </AuthGuard>
          } />

          {/* Error routes */}
          <Route path="/unauthorized" element={
            <AppLayout>
              <UnauthorizedPage />
            </AppLayout>
          } />
          
          <Route path="*" element={
            <AppLayout>
              <NotFoundPage />
            </AppLayout>
          } />
        </Routes>
      </Router>
    </AccessibilityProvider>
  )
}

export default App