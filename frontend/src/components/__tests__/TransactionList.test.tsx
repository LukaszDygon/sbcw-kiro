import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TransactionList from '../TransactionList';
import { TestWrapper, mockUser } from '../../test-utils/auth-test-utils';
import { setMockAuthState, resetMockAuthState } from '../__mocks__/AuthGuard';
import { transactionsService } from '../../services/transactions';

// Mock the services
jest.mock('../../services/transactions');

const mockedTransactionsService = transactionsService as jest.Mocked<typeof transactionsService>;

describe('TransactionList Component', () => {
  const mockTransactions = [
    {
      id: '1',
      amount: '25.00',
      sender_name: 'John Doe',
      recipient_name: 'Jane Smith',
      note: 'Lunch payment',
      category: 'Food',
      created_at: '2024-01-15T12:00:00Z',
      transaction_type: 'transfer',
      status: 'completed'
    },
    {
      id: '2',
      amount: '50.00',
      sender_name: 'Jane Smith',
      recipient_name: 'John Doe',
      note: 'Dinner split',
      category: 'Food',
      created_at: '2024-01-14T19:30:00Z',
      transaction_type: 'transfer',
      status: 'completed'
    },
    {
      id: '3',
      amount: '30.00',
      sender_name: 'John Doe',
      recipient_name: 'Event: Team Lunch',
      note: 'Team lunch contribution',
      category: 'Events',
      created_at: '2024-01-13T10:15:00Z',
      transaction_type: 'event_contribution',
      status: 'completed'
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    resetMockAuthState();
    
    // Set authenticated state
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    });

    mockedTransactionsService.getTransactionHistory.mockResolvedValue({
      transactions: mockTransactions,
      pagination: {
        page: 1,
        limit: 10,
        total: 3,
        total_pages: 1
      }
    });
  });

  it('renders transaction list', async () => {
    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    expect(screen.getByText(/transaction history/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
      expect(screen.getByText('Dinner split')).toBeInTheDocument();
      expect(screen.getByText('Team lunch contribution')).toBeInTheDocument();
    });
  });

  it('displays transaction details correctly', async () => {
    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      // Check amounts
      expect(screen.getByText('£25.00')).toBeInTheDocument();
      expect(screen.getByText('£50.00')).toBeInTheDocument();
      expect(screen.getByText('£30.00')).toBeInTheDocument();

      // Check participants
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();

      // Check categories
      expect(screen.getAllByText('Food')).toHaveLength(2);
      expect(screen.getByText('Events')).toBeInTheDocument();

      // Check dates (formatted)
      expect(screen.getByText(/Jan 15, 2024/)).toBeInTheDocument();
      expect(screen.getByText(/Jan 14, 2024/)).toBeInTheDocument();
      expect(screen.getByText(/Jan 13, 2024/)).toBeInTheDocument();
    });
  });

  it('filters transactions by date range', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
    });

    // Set date filters
    const startDateInput = screen.getByLabelText(/start date/i);
    const endDateInput = screen.getByLabelText(/end date/i);

    await user.type(startDateInput, '2024-01-14');
    await user.type(endDateInput, '2024-01-15');

    const applyFiltersButton = screen.getByRole('button', { name: /apply filters/i });
    await user.click(applyFiltersButton);

    await waitFor(() => {
      expect(mockedTransactionsService.getTransactionHistory).toHaveBeenCalledWith({
        start_date: '2024-01-14',
        end_date: '2024-01-15',
        page: 1,
        limit: 10
      });
    });
  });

  it('filters transactions by amount range', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
    });

    const minAmountInput = screen.getByLabelText(/minimum amount/i);
    const maxAmountInput = screen.getByLabelText(/maximum amount/i);

    await user.type(minAmountInput, '30');
    await user.type(maxAmountInput, '60');

    const applyFiltersButton = screen.getByRole('button', { name: /apply filters/i });
    await user.click(applyFiltersButton);

    await waitFor(() => {
      expect(mockedTransactionsService.getTransactionHistory).toHaveBeenCalledWith({
        min_amount: '30',
        max_amount: '60',
        page: 1,
        limit: 10
      });
    });
  });

  it('filters transactions by category', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
    });

    const categorySelect = screen.getByLabelText(/category/i);
    await user.selectOptions(categorySelect, 'Food');

    const applyFiltersButton = screen.getByRole('button', { name: /apply filters/i });
    await user.click(applyFiltersButton);

    await waitFor(() => {
      expect(mockedTransactionsService.getTransactionHistory).toHaveBeenCalledWith({
        category: 'Food',
        page: 1,
        limit: 10
      });
    });
  });

  it('searches transactions by text', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search transactions/i);
    await user.type(searchInput, 'lunch');

    // Search should trigger automatically after typing
    await waitFor(() => {
      expect(mockedTransactionsService.getTransactionHistory).toHaveBeenCalledWith({
        search: 'lunch',
        page: 1,
        limit: 10
      });
    });
  });

  it('sorts transactions by different criteria', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
    });

    const sortSelect = screen.getByLabelText(/sort by/i);
    await user.selectOptions(sortSelect, 'amount_desc');

    await waitFor(() => {
      expect(mockedTransactionsService.getTransactionHistory).toHaveBeenCalledWith({
        sort_by: 'amount',
        sort_order: 'desc',
        page: 1,
        limit: 10
      });
    });
  });

  it('handles pagination', async () => {
    const user = userEvent.setup();

    // Mock response with multiple pages
    mockedTransactionsService.getTransactionHistory.mockResolvedValue({
      transactions: mockTransactions,
      pagination: {
        page: 1,
        limit: 10,
        total: 25,
        total_pages: 3
      }
    });

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
    });

    // Check pagination controls
    expect(screen.getByText(/page 1 of 3/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next page/i })).toBeInTheDocument();

    // Click next page
    const nextButton = screen.getByRole('button', { name: /next page/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(mockedTransactionsService.getTransactionHistory).toHaveBeenCalledWith({
        page: 2,
        limit: 10
      });
    });
  });

  it('shows transaction details in modal when clicked', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
    });

    // Click on a transaction
    const transactionRow = screen.getByText('Lunch payment').closest('tr');
    await user.click(transactionRow!);

    // Check modal appears
    await waitFor(() => {
      expect(screen.getByText(/transaction details/i)).toBeInTheDocument();
      expect(screen.getByText('Transaction ID: 1')).toBeInTheDocument();
      expect(screen.getByText('Amount: £25.00')).toBeInTheDocument();
      expect(screen.getByText('From: John Doe')).toBeInTheDocument();
      expect(screen.getByText('To: Jane Smith')).toBeInTheDocument();
    });
  });

  it('exports transactions to CSV', async () => {
    const user = userEvent.setup();

    mockedTransactionsService.exportTransactions.mockResolvedValue({
      success: true,
      data: 'Date,Amount,From,To,Note\n2024-01-15,25.00,John Doe,Jane Smith,Lunch payment',
      format: 'csv'
    });

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
    });

    const exportButton = screen.getByRole('button', { name: /export/i });
    await user.click(exportButton);

    const csvOption = screen.getByText(/csv/i);
    await user.click(csvOption);

    await waitFor(() => {
      expect(mockedTransactionsService.exportTransactions).toHaveBeenCalledWith({
        format: 'csv',
        filters: {}
      });
    });
  });

  it('shows loading state', () => {
    mockedTransactionsService.getTransactionHistory.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    expect(screen.getByText(/loading transactions/i)).toBeInTheDocument();
  });

  it('shows error state when fetch fails', async () => {
    mockedTransactionsService.getTransactionHistory.mockRejectedValue(
      new Error('Network error')
    );

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/error loading transactions/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no transactions', async () => {
    mockedTransactionsService.getTransactionHistory.mockResolvedValue({
      transactions: [],
      pagination: {
        page: 1,
        limit: 10,
        total: 0,
        total_pages: 0
      }
    });

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/no transactions found/i)).toBeInTheDocument();
    });
  });

  it('clears all filters', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Lunch payment')).toBeInTheDocument();
    });

    // Apply some filters
    const searchInput = screen.getByPlaceholderText(/search transactions/i);
    await user.type(searchInput, 'lunch');

    const categorySelect = screen.getByLabelText(/category/i);
    await user.selectOptions(categorySelect, 'Food');

    // Clear filters
    const clearFiltersButton = screen.getByRole('button', { name: /clear filters/i });
    await user.click(clearFiltersButton);

    // Check that inputs are cleared
    expect(searchInput).toHaveValue('');
    expect(categorySelect).toHaveValue('');

    // Check that API is called with no filters
    await waitFor(() => {
      expect(mockedTransactionsService.getTransactionHistory).toHaveBeenCalledWith({
        page: 1,
        limit: 10
      });
    });
  });

  it('displays transaction type icons correctly', async () => {
    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      // Check for transfer icons
      const transferIcons = screen.getAllByTestId('transfer-icon');
      expect(transferIcons).toHaveLength(2);

      // Check for event contribution icon
      const eventIcon = screen.getByTestId('event-icon');
      expect(eventIcon).toBeInTheDocument();
    });
  });

  it('shows different styling for sent vs received transactions', async () => {
    // Mock current user context
    const mockCurrentUser = { id: 'current-user', name: 'Current User' };
    
    const transactionsWithCurrentUser = [
      {
        ...mockTransactions[0],
        sender_id: 'current-user', // Sent by current user
        recipient_id: 'other-user'
      },
      {
        ...mockTransactions[1],
        sender_id: 'other-user', // Received by current user
        recipient_id: 'current-user'
      }
    ];

    mockedTransactionsService.getTransactionHistory.mockResolvedValue({
      transactions: transactionsWithCurrentUser,
      pagination: {
        page: 1,
        limit: 10,
        total: 2,
        total_pages: 1
      }
    });

    render(
      <TestWrapper>
        <TransactionList />
      </TestWrapper>
    );

    await waitFor(() => {
      // Check for sent transaction styling (red/negative)
      const sentTransaction = screen.getByText('Lunch payment').closest('tr');
      expect(sentTransaction).toHaveClass('transaction-sent');

      // Check for received transaction styling (green/positive)
      const receivedTransaction = screen.getByText('Dinner split').closest('tr');
      expect(receivedTransaction).toHaveClass('transaction-received');
    });
  });
});