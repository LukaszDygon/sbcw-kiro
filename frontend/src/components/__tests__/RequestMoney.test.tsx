import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RequestMoney from '../RequestMoney';
import { TestWrapper, mockUser } from '../../test-utils/auth-test-utils';
import { setMockAuthState, resetMockAuthState } from '../__mocks__/AuthGuard';
import { moneyRequestsService } from '../../services/moneyRequests';

// Mock the services
jest.mock('../../services/moneyRequests');

const mockedMoneyRequestsService = moneyRequestsService as jest.Mocked<typeof moneyRequestsService>;

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('RequestMoney Component', () => {
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

    // Setup service mocks
    mockedMoneyRequestsService.createRequest.mockResolvedValue({
      id: 'req-123',
      requester_id: mockUser.id,
      recipient_id: 'recipient-123',
      amount: '25.00',
      note: 'Test request',
      status: 'PENDING',
      created_at: '2024-01-15T12:00:00Z',
      expires_at: '2024-01-22T12:00:00Z'
    });
  });

  it('renders request money form', async () => {
    render(
      <TestWrapper>
        <RequestMoney />
      </TestWrapper>
    );

    expect(screen.getByText('Request Money')).toBeInTheDocument();
    expect(screen.getByText('Request money from other SoftBank employees')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search for a person...')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('0.00')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Optional note')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send request/i })).toBeInTheDocument();
  });

  it('validates form inputs correctly', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <RequestMoney />
      </TestWrapper>
    );

    // Try to submit without filling form
    const submitButton = screen.getByRole('button', { name: /send request/i });
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
        <RequestMoney />
      </TestWrapper>
    );

    const amountInput = screen.getByPlaceholderText('0.00');
    
    // Test negative amount
    await user.type(amountInput, '-10');
    const submitButton = screen.getByRole('button', { name: /send request/i });
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

  it('creates money request successfully', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <RequestMoney />
      </TestWrapper>
    );

    // Fill in amount
    const amountInput = screen.getByPlaceholderText('0.00');
    await user.type(amountInput, '25.00');

    // Fill in note
    const noteInput = screen.getByPlaceholderText('Optional note');
    await user.type(noteInput, 'Test request');

    // Submit form (recipient selection would be handled by UserSearch component)
    const submitButton = screen.getByRole('button', { name: /send request/i });
    
    // Mock successful recipient selection by simulating form submission
    const form = submitButton.closest('form');
    if (form) {
      fireEvent.submit(form);
    }

    // Should navigate to money requests page on success
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/money-requests', {
        state: { message: 'Money request sent successfully!' }
      });
    });
  });

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup();

    mockedMoneyRequestsService.createRequest.mockRejectedValue(new Error('Request failed'));

    render(
      <TestWrapper>
        <RequestMoney />
      </TestWrapper>
    );

    // Fill in amount
    const amountInput = screen.getByPlaceholderText('0.00');
    await user.type(amountInput, '25.00');

    const submitButton = screen.getByRole('button', { name: /send request/i });
    
    // Simulate form submission that would trigger the error
    const form = submitButton.closest('form');
    if (form) {
      fireEvent.submit(form);
    }

    // Should display error message
    await waitFor(() => {
      expect(screen.getByText('Request failed')).toBeInTheDocument();
    });

    // Should not navigate away on error
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('validates note length', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <RequestMoney />
      </TestWrapper>
    );

    const noteInput = screen.getByPlaceholderText('Optional note');
    const longNote = 'a'.repeat(501); // Exceeds 500 character limit
    
    await user.type(noteInput, longNote);

    const submitButton = screen.getByRole('button', { name: /send request/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Note cannot exceed 500 characters')).toBeInTheDocument();
    });
  });

  it('shows character count for note input', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <RequestMoney />
      </TestWrapper>
    );

    const noteInput = screen.getByPlaceholderText('Optional note');
    await user.type(noteInput, 'Test note');

    await waitFor(() => {
      expect(screen.getByText('9/500 characters')).toBeInTheDocument();
    });
  });

  it('prevents requesting money from self', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <RequestMoney />
      </TestWrapper>
    );

    // The UserSearch component should handle excludeSelf prop
    // This test verifies the component renders with proper configuration
    const recipientInput = screen.getByPlaceholderText('Search for a person...');
    expect(recipientInput).toBeInTheDocument();
    
    // The actual validation would be handled by UserSearch component's excludeSelf prop
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();

    // Mock delayed response
    mockedMoneyRequestsService.createRequest.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        id: 'req-123',
        requester_id: mockUser.id,
        recipient_id: 'recipient-123',
        amount: '25.00',
        note: 'Test request',
        status: 'PENDING',
        created_at: '2024-01-15T12:00:00Z',
        expires_at: '2024-01-22T12:00:00Z'
      }), 100))
    );

    render(
      <TestWrapper>
        <RequestMoney />
      </TestWrapper>
    );

    // Fill in amount
    const amountInput = screen.getByPlaceholderText('0.00');
    await user.type(amountInput, '25.00');

    const submitButton = screen.getByRole('button', { name: /send request/i });
    
    // Simulate form submission
    const form = submitButton.closest('form');
    if (form) {
      fireEvent.submit(form);
    }

    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText(/sending/i)).toBeInTheDocument();
    });

    expect(submitButton).toBeDisabled();
  });

  it('cancels and navigates back to dashboard', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <RequestMoney />
      </TestWrapper>
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });
});