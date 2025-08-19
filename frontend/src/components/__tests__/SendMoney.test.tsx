import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SendMoney from '../SendMoney';
import { TestWrapper, mockUser } from '../../test-utils/auth-test-utils';
import { setMockAuthState, resetMockAuthState } from '../__mocks__/AuthGuard';

// Mock the services at the module level
const mockTransactionsService = {
  getCategories: jest.fn(),
  sendMoney: jest.fn(),
  sendBulkMoney: jest.fn(),
};

const mockAccountsService = {
  getBalance: jest.fn(),
};

jest.mock('../../services/transactions', () => ({
  transactionsService: mockTransactionsService,
}));

jest.mock('../../services/accounts', () => ({
  accountsService: mockAccountsService,
}));

// Mock UserSearch component to simplify testing
jest.mock('../UserSearch', () => {
  return function MockUserSearch({ onUserSelect, selectedUser, placeholder, className }: any) {
    return (
      <div className={`relative ${className}`}>
        <input
          placeholder={placeholder}
          value={selectedUser?.name || ''}
          onChange={(e) => {
            if (e.target.value === 'John Doe') {
              onUserSelect({ id: 'user-1', name: 'John Doe', email: 'john@example.com', role: 'EMPLOYEE' });
            } else if (e.target.value === '') {
              onUserSelect(null);
            }
          }}
          data-testid="user-search-input"
        />
      </div>
    );
  };
});

const mockedTransactionsService = transactionsService as jest.Mocked<typeof transactionsService>;
const mockedAccountsService = accountsService as jest.Mocked<typeof accountsService>;

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('SendMoney Component', () => {
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

    // Setup service mocks with proper return values
    mockedTransactionsService.getCategories.mockResolvedValue({
      categories: [
        { id: '1', name: 'Food' },
        { id: '2', name: 'Transport' }
      ]
    });
    
    mockedAccountsService.getBalance.mockResolvedValue({
      balance: '150.00',
      available_balance: '150.00',
      currency: 'GBP',
      limits: {
        minimum_balance: '-250.00',
        maximum_balance: '250.00',
        overdraft_limit: '250.00'
      }
    });

    // Mock sendMoney for successful tests
    mockedTransactionsService.sendMoney.mockResolvedValue({
      id: 'trans-123',
      amount: '25.00',
      recipient_name: 'John Doe',
      sender_name: 'Test User',
      note: 'Test payment',
      created_at: '2024-01-15T12:00:00Z',
      status: 'COMPLETED',
      transaction_type: 'TRANSFER'
    });
  });

  it('renders send money form structure', async () => {
    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    // Wait for component to load and balance to be displayed
    await waitFor(() => {
      expect(screen.getByText('Send Money')).toBeInTheDocument();
      expect(screen.getByText('£150.00')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Check basic form structure
    expect(screen.getByText('Transfer money to other SoftBank employees')).toBeInTheDocument();
    expect(screen.getByText('Available Balance')).toBeInTheDocument();
    expect(screen.getByText('Add Recipient')).toBeInTheDocument();
    expect(screen.getByText('Recipient 1')).toBeInTheDocument();
    expect(screen.getByTestId('user-search-input')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('0.00')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Optional note')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('validates form inputs correctly', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Send Money')).toBeInTheDocument();
    });

    // Try to submit without filling form
    const submitButton = screen.getByRole('button', { name: /send/i });
    await user.click(submitButton);

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText('Please select a recipient')).toBeInTheDocument();
      expect(screen.getByText('Amount is required')).toBeInTheDocument();
    });
  });

  it('validates amount input with proper error messages', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Send Money')).toBeInTheDocument();
    });

    const amountInput = screen.getByPlaceholderText('0.00');
    
    // Test negative amount
    await user.type(amountInput, '-10');
    const submitButton = screen.getByRole('button', { name: /send/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Amount must be greater than 0')).toBeInTheDocument();
    });

    // Test zero amount
    await user.clear(amountInput);
    await user.type(amountInput, '0');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Amount must be greater than 0')).toBeInTheDocument();
    });

    // Test amount exceeding limit
    await user.clear(amountInput);
    await user.type(amountInput, '15000');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Amount cannot exceed £10,000')).toBeInTheDocument();
    });
  });

  it('adds and removes recipients for bulk transfer', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Send Money')).toBeInTheDocument();
    });

    // Initially should show one recipient
    expect(screen.getByText('Recipient 1')).toBeInTheDocument();
    expect(screen.queryByText('Recipient 2')).not.toBeInTheDocument();

    // Add a recipient
    const addButton = screen.getByText('Add Recipient');
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('Recipient 2')).toBeInTheDocument();
      expect(screen.getByText('Recipients')).toBeInTheDocument(); // Should change to plural
    });

    // Should now have remove buttons (trash icons)
    const removeButtons = screen.getAllByRole('button');
    const trashButtons = removeButtons.filter(button => 
      button.querySelector('svg path[d*="M19 7l-.867 12.142"]')
    );
    expect(trashButtons.length).toBeGreaterThan(0);
  });

  it('shows character count for note input', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Send Money')).toBeInTheDocument();
    });

    const noteInput = screen.getByPlaceholderText('Optional note');
    await user.type(noteInput, 'Test note');

    await waitFor(() => {
      expect(screen.getByText('9/500 characters')).toBeInTheDocument();
    });
  });

  it('displays total amount when amount is entered', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Send Money')).toBeInTheDocument();
    });

    // Enter amount
    const amountInput = screen.getByPlaceholderText('0.00');
    await user.type(amountInput, '50.00');

    // Should show total to send
    await waitFor(() => {
      expect(screen.getByText('Total to Send')).toBeInTheDocument();
      expect(screen.getByText('£50.00')).toBeInTheDocument();
    });
  });

  it('handles successful form submission with recipient selection', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    // Wait for balance to load first
    await waitFor(() => {
      expect(screen.getByText('£150.00')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Select recipient using mock UserSearch
    const recipientInput = screen.getByTestId('user-search-input');
    await user.type(recipientInput, 'John Doe');

    // Fill in amount
    const amountInput = screen.getByPlaceholderText('0.00');
    await user.type(amountInput, '25.00');

    // Fill in note
    const noteInput = screen.getByPlaceholderText('Optional note');
    await user.type(noteInput, 'Test payment');

    // Submit form
    const submitButton = screen.getByRole('button', { name: /send £25.00/i });
    await user.click(submitButton);

    // Should call the service
    await waitFor(() => {
      expect(mockedTransactionsService.sendMoney).toHaveBeenCalledWith({
        recipient_id: 'user-1',
        amount: '25.00',
        note: 'Test payment',
        category: undefined
      });
    });

    // Should navigate to transaction history on success
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/transactions/history', {
        state: { message: 'Money sent successfully!' }
      });
    });
  });

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup();

    // Override the default mock to return an error
    mockedTransactionsService.sendMoney.mockRejectedValue(new Error('Insufficient funds'));

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    // Wait for balance to load first
    await waitFor(() => {
      expect(screen.getByText('£150.00')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Select recipient and fill form
    const recipientInput = screen.getByTestId('user-search-input');
    await user.type(recipientInput, 'John Doe');

    const amountInput = screen.getByPlaceholderText('0.00');
    await user.type(amountInput, '25.00');

    const submitButton = screen.getByRole('button', { name: /send £25.00/i });
    await user.click(submitButton);

    // Should display error message
    await waitFor(() => {
      expect(screen.getByText('Insufficient funds')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Should not navigate away on error
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();

    // Mock delayed response
    mockedTransactionsService.sendMoney.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        id: 'trans-123',
        amount: '25.00',
        recipient_name: 'John Doe',
        sender_name: 'Test User',
        note: 'Test payment',
        created_at: '2024-01-15T12:00:00Z',
        status: 'COMPLETED',
        transaction_type: 'TRANSFER'
      }), 200))
    );

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    // Wait for balance to load first
    await waitFor(() => {
      expect(screen.getByText('£150.00')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Fill form
    const recipientInput = screen.getByTestId('user-search-input');
    await user.type(recipientInput, 'John Doe');

    const amountInput = screen.getByPlaceholderText('0.00');
    await user.type(amountInput, '25.00');

    const submitButton = screen.getByRole('button', { name: /send £25.00/i });
    await user.click(submitButton);

    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText('Sending...')).toBeInTheDocument();
    });

    expect(submitButton).toBeDisabled();
  });

  it('cancels and navigates back to dashboard', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Send Money')).toBeInTheDocument();
    });

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('handles initial data loading failure', async () => {
    mockedAccountsService.getBalance.mockRejectedValue(new Error('Network error'));
    mockedTransactionsService.getCategories.mockRejectedValue(new Error('Network error'));

    render(
      <TestWrapper>
        <SendMoney />
      </TestWrapper>
    );

    // Should show error in the error display section
    await waitFor(() => {
      expect(screen.getByText('Failed to load required data')).toBeInTheDocument();
    });
  });
});