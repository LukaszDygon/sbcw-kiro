/**
 * Integration tests for the complete application workflow
 * Tests user flows from login to transaction completion
 */
import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '../../components/Dashboard'
import * as authService from '../../services/auth'
import * as accountsService from '../../services/accounts'
import * as transactionsService from '../../services/transactions'
import * as eventsService from '../../services/events'
import * as moneyRequestsService from '../../services/moneyRequests'

// Mock all services
jest.mock('../../services/auth')
jest.mock('../../services/accounts')
jest.mock('../../services/transactions')
jest.mock('../../services/events')
jest.mock('../../services/moneyRequests')

const mockedAuthService = authService as jest.Mocked<typeof authService>
const mockedAccountsService = accountsService as jest.Mocked<typeof accountsService>
const mockedTransactionsService = transactionsService as jest.Mocked<typeof transactionsService>
const mockedEventsService = eventsService as jest.Mocked<typeof eventsService>
const mockedMoneyRequestsService = moneyRequestsService as jest.Mocked<typeof moneyRequestsService>

// Mock user data
const mockUser = {
  id: '1',
  microsoft_id: 'test@softbank.com',
  email: 'test@softbank.com',
  name: 'Test User',
  role: 'EMPLOYEE' as const,
  account_status: 'ACTIVE' as const,
  created_at: '2023-01-01T00:00:00Z',
  last_login: '2023-01-01T00:00:00Z'
}

const mockBalance = {
  balance: '150.00',
  available_balance: '100.00',
  currency: 'GBP'
}

const mockTransactions = {
  transactions: [
    {
      id: '1',
      sender_id: '1',
      recipient_id: '2',
      sender_name: 'Test User',
      recipient_name: 'John Doe',
      amount: '25.00',
      transaction_type: 'TRANSFER',
      note: 'Test transaction',
      status: 'COMPLETED',
      created_at: '2023-01-01T12:00:00Z'
    }
  ],
  total: 1,
  page: 1,
  per_page: 10
}

const mockEvents = {
  events: [
    {
      id: '1',
      creator_id: '1',
      name: 'Team Lunch',
      description: 'Monthly team lunch',
      target_amount: '200.00',
      total_contributions: '150.00',
      status: 'ACTIVE',
      created_at: '2023-01-01T00:00:00Z'
    }
  ]
}

const mockRequests = {
  requests: [
    {
      id: '1',
      requester_id: '2',
      recipient_id: '1',
      requester_name: 'John Doe',
      amount: '30.00',
      note: 'Lunch money',
      status: 'PENDING',
      created_at: '2023-01-01T10:00:00Z'
    }
  ]
}

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Dashboard Integration Tests', () => {
  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks()
    
    // Setup default auth service mocks
    mockedAuthService.isAuthenticated.mockReturnValue(true)
    mockedAuthService.getAuthState.mockReturnValue({
      isAuthenticated: true,
      user: mockUser,
      isLoading: false,
      error: null
    })
    mockedAuthService.initialize.mockResolvedValue(mockUser)
    mockedAuthService.hasRole.mockReturnValue(true)
    mockedAuthService.hasAnyRole.mockReturnValue(true)
    mockedAuthService.hasPermission.mockReturnValue(true)
    mockedAuthService.hasAnyPermission.mockReturnValue(true)
    mockedAuthService.hasAllPermissions.mockReturnValue(true)
    mockedAuthService.isAdmin.mockReturnValue(false)
    mockedAuthService.isFinance.mockReturnValue(false)
    
    // Setup service mocks
    mockedAccountsService.getBalance.mockResolvedValue(mockBalance)
    mockedTransactionsService.getRecentTransactions.mockResolvedValue(mockTransactions)
    mockedEventsService.getActiveEvents.mockResolvedValue(mockEvents)
    mockedMoneyRequestsService.getPendingRequests.mockResolvedValue(mockRequests)
    mockedAccountsService.getSpendingAnalytics.mockResolvedValue({
      total_spent: '75.00',
      total_received: '100.00'
    })
  })

  describe('Dashboard Component Integration', () => {
    it('shows dashboard for authenticated users', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Welcome back, Test!')).toBeInTheDocument()
      })
    })
  })

  describe('Dashboard Integration', () => {
    it('loads and displays dashboard data correctly', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Welcome back, Test!')).toBeInTheDocument()
        expect(screen.getByText('£150.00')).toBeInTheDocument()
        expect(screen.getByText('Available: £100.00')).toBeInTheDocument()
      })

      // Check that services were called
      expect(mockedAccountsService.getBalance).toHaveBeenCalled()
      expect(mockedTransactionsService.getRecentTransactions).toHaveBeenCalledWith(5)
      expect(mockedEventsService.getActiveEvents).toHaveBeenCalled()
      expect(mockedMoneyRequestsService.getPendingRequests).toHaveBeenCalled()
    })

    it('displays recent transactions', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Recent Transactions')).toBeInTheDocument()
        expect(screen.getByText('To John Doe')).toBeInTheDocument()
        expect(screen.getByText('-£25.00')).toBeInTheDocument()
      })
    })

    it('shows quick action buttons', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Send Money')).toBeInTheDocument()
        expect(screen.getByText('Request Money')).toBeInTheDocument()
        expect(screen.getByText('View Events')).toBeInTheDocument()
        expect(screen.getByText('View Reports')).toBeInTheDocument()
      })
    })
  })

  describe('Navigation Integration', () => {
    it('navigates to send money page', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Send Money')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Send Money'))

      await waitFor(() => {
        expect(window.location.pathname).toBe('/transactions/send')
      })
    })

    it('navigates to events page', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('View Events')).toBeInTheDocument()
      })

      await user.click(screen.getByText('View Events'))

      await waitFor(() => {
        expect(window.location.pathname).toBe('/events/active')
      })
    })
  })

  describe('Role-Based Access Control', () => {
    it('shows admin panel for admin users', async () => {
      mockedAuthService.isAdmin.mockReturnValue(true)
      mockedAuthService.hasRole.mockImplementation((role) => role === 'ADMIN')
      
      // Navigate directly to admin route
      window.history.pushState({}, '', '/admin')
      
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Admin Panel')).toBeInTheDocument()
      })
    })

    it('blocks admin panel for regular users', async () => {
      mockedAuthService.isAdmin.mockReturnValue(false)
      mockedAuthService.hasRole.mockImplementation((role) => role === 'EMPLOYEE')
      
      // Navigate directly to admin route
      window.history.pushState({}, '', '/admin')
      
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Access Denied')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      mockedAccountsService.getBalance.mockRejectedValue(new Error('Network error'))
      
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Error Loading Dashboard')).toBeInTheDocument()
        expect(screen.getByText('Network error')).toBeInTheDocument()
      })
    })

    it('shows loading states', async () => {
      // Delay the API response
      mockedAccountsService.getBalance.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve(mockBalance), 100))
      )
      
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      expect(screen.getByText('Loading dashboard...')).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByText('Welcome back, Test!')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility Integration', () => {
    it('provides skip to main content link', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      const skipLink = screen.getByText('Skip to main content')
      expect(skipLink).toBeInTheDocument()
      expect(skipLink).toHaveAttribute('href', '#main-content')
    })

    it('has proper ARIA labels and roles', async () => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument()
        expect(screen.getByRole('main')).toBeInTheDocument()
        expect(screen.getByRole('navigation', { name: 'Main navigation' })).toBeInTheDocument()
      })
    })

    it('opens accessibility settings', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        const settingsButton = screen.getByLabelText('Open accessibility settings')
        expect(settingsButton).toBeInTheDocument()
      })

      await user.click(screen.getByLabelText('Open accessibility settings'))

      await waitFor(() => {
        expect(screen.getByText('Accessibility Settings')).toBeInTheDocument()
      })
    })
  })

  describe('Notification Integration', () => {
    it('opens notification center', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        const notificationButton = screen.getByLabelText(/notifications/i)
        expect(notificationButton).toBeInTheDocument()
      })

      await user.click(screen.getByLabelText(/notifications/i))

      await waitFor(() => {
        expect(screen.getByText('Notifications')).toBeInTheDocument()
      })
    })
  })

  describe('Logout Integration', () => {
    it('logs out user successfully', async () => {
      const user = userEvent.setup()
      mockedAuthService.logout.mockResolvedValue(undefined)
      
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Logout')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Logout'))

      expect(mockedAuthService.logout).toHaveBeenCalled()
    })
  })
})