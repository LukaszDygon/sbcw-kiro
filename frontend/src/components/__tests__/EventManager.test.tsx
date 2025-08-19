import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EventManager from '../EventManager';
import { TestWrapper, mockUser } from '../../test-utils/auth-test-utils';
import { setMockAuthState, resetMockAuthState } from '../__mocks__/AuthGuard';
import { eventsService } from '../../services/events';

// Mock the services
jest.mock('../../services/events');

const mockedEventsService = eventsService as jest.Mocked<typeof eventsService>;

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('EventManager Component', () => {
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
    mockedEventsService.createEvent.mockResolvedValue({
      id: 'event-123',
      creator_id: mockUser.id,
      name: 'Team Lunch',
      description: 'Monthly team lunch',
      target_amount: '100.00',
      deadline: '2024-02-15T12:00:00Z',
      status: 'ACTIVE',
      total_contributions: '0.00',
      created_at: '2024-01-15T12:00:00Z'
    });
  });

  it('renders event creation form', async () => {
    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    expect(screen.getByText('Create Event')).toBeInTheDocument();
    expect(screen.getByText('Create a new event account for collective funding')).toBeInTheDocument();
    expect(screen.getByLabelText(/event name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/target amount/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/deadline/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create event/i })).toBeInTheDocument();
  });

  it('validates form inputs correctly', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    // Try to submit without filling required fields
    const submitButton = screen.getByRole('button', { name: /create event/i });
    await user.click(submitButton);

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText('Event name is required')).toBeInTheDocument();
      expect(screen.getByText('Description is required')).toBeInTheDocument();
    });
  });

  it('validates event name length', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    const nameInput = screen.getByLabelText(/event name/i);
    
    // Test name too short
    await user.type(nameInput, 'ab');
    const submitButton = screen.getByRole('button', { name: /create event/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Event name must be at least 3 characters')).toBeInTheDocument();
    });

    // Test name too long
    await user.clear(nameInput);
    const longName = 'a'.repeat(101); // Exceeds 100 character limit
    await user.type(nameInput, longName);
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Event name cannot exceed 100 characters')).toBeInTheDocument();
    });
  });

  it('validates description length', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    const descriptionInput = screen.getByLabelText(/description/i);
    const longDescription = 'a'.repeat(1001); // Exceeds 1000 character limit
    
    await user.type(descriptionInput, longDescription);

    const submitButton = screen.getByRole('button', { name: /create event/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Description cannot exceed 1000 characters')).toBeInTheDocument();
    });
  });

  it('validates target amount', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    const targetAmountInput = screen.getByLabelText(/target amount/i);
    
    // Test negative amount
    await user.type(targetAmountInput, '-10');
    const submitButton = screen.getByRole('button', { name: /create event/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Target amount must be greater than 0')).toBeInTheDocument();
    });

    // Test zero amount
    await user.clear(targetAmountInput);
    await user.type(targetAmountInput, '0');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Target amount must be greater than 0')).toBeInTheDocument();
    });

    // Test amount exceeding limit
    await user.clear(targetAmountInput);
    await user.type(targetAmountInput, '50000');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Target amount cannot exceed £50,000')).toBeInTheDocument();
    });
  });

  it('validates deadline is in the future', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    const deadlineInput = screen.getByLabelText(/deadline/i);
    
    // Set deadline to yesterday
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayString = yesterday.toISOString().split('T')[0];
    
    await user.type(deadlineInput, yesterdayString);
    const submitButton = screen.getByRole('button', { name: /create event/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Deadline must be in the future')).toBeInTheDocument();
    });
  });

  it('creates event successfully', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    // Fill in required fields
    const nameInput = screen.getByLabelText(/event name/i);
    await user.type(nameInput, 'Team Lunch');

    const descriptionInput = screen.getByLabelText(/description/i);
    await user.type(descriptionInput, 'Monthly team lunch');

    const targetAmountInput = screen.getByLabelText(/target amount/i);
    await user.type(targetAmountInput, '100.00');

    const deadlineInput = screen.getByLabelText(/deadline/i);
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 30);
    const futureDateString = futureDate.toISOString().split('T')[0];
    await user.type(deadlineInput, futureDateString);

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create event/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockedEventsService.createEvent).toHaveBeenCalledWith({
        name: 'Team Lunch',
        description: 'Monthly team lunch',
        target_amount: '100.00',
        deadline: expect.any(String)
      });
    });

    // Should navigate to events page on success
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/events', {
        state: { message: 'Event created successfully!' }
      });
    });
  });

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup();

    mockedEventsService.createEvent.mockRejectedValue(new Error('Event creation failed'));

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    // Fill in required fields
    const nameInput = screen.getByLabelText(/event name/i);
    await user.type(nameInput, 'Team Lunch');

    const descriptionInput = screen.getByLabelText(/description/i);
    await user.type(descriptionInput, 'Monthly team lunch');

    const submitButton = screen.getByRole('button', { name: /create event/i });
    await user.click(submitButton);

    // Should display error message
    await waitFor(() => {
      expect(screen.getByText('Event creation failed')).toBeInTheDocument();
    });

    // Should not navigate away on error
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('shows character count for text inputs', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    const nameInput = screen.getByLabelText(/event name/i);
    await user.type(nameInput, 'Team Lunch');

    await waitFor(() => {
      expect(screen.getByText('10/100 characters')).toBeInTheDocument();
    });

    const descriptionInput = screen.getByLabelText(/description/i);
    await user.type(descriptionInput, 'Monthly team lunch');

    await waitFor(() => {
      expect(screen.getByText('18/1000 characters')).toBeInTheDocument();
    });
  });

  it('shows loading state during submission', async () => {
    const user = userEvent.setup();

    // Mock delayed response
    mockedEventsService.createEvent.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        id: 'event-123',
        creator_id: mockUser.id,
        name: 'Team Lunch',
        description: 'Monthly team lunch',
        target_amount: '100.00',
        deadline: '2024-02-15T12:00:00Z',
        status: 'ACTIVE',
        total_contributions: '0.00',
        created_at: '2024-01-15T12:00:00Z'
      }), 100))
    );

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    // Fill in required fields
    const nameInput = screen.getByLabelText(/event name/i);
    await user.type(nameInput, 'Team Lunch');

    const descriptionInput = screen.getByLabelText(/description/i);
    await user.type(descriptionInput, 'Monthly team lunch');

    const submitButton = screen.getByRole('button', { name: /create event/i });
    await user.click(submitButton);

    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText(/creating/i)).toBeInTheDocument();
    });

    expect(submitButton).toBeDisabled();
  });

  it('allows optional fields to be empty', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    // Fill in only required fields
    const nameInput = screen.getByLabelText(/event name/i);
    await user.type(nameInput, 'Team Lunch');

    const descriptionInput = screen.getByLabelText(/description/i);
    await user.type(descriptionInput, 'Monthly team lunch');

    // Leave target amount and deadline empty
    const submitButton = screen.getByRole('button', { name: /create event/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockedEventsService.createEvent).toHaveBeenCalledWith({
        name: 'Team Lunch',
        description: 'Monthly team lunch',
        target_amount: undefined,
        deadline: undefined
      });
    });
  });

  it('cancels and navigates back to events', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/events');
  });

  it('formats currency input correctly', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <EventManager />
      </TestWrapper>
    );

    const targetAmountInput = screen.getByLabelText(/target amount/i);
    await user.type(targetAmountInput, '1234.56');

    // Should accept decimal input
    expect(targetAmountInput).toHaveValue(1234.56);
  });
});