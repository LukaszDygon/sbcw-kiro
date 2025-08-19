import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdminPanel from '../AdminPanel';
import { TestWrapper, mockAdminUser } from '../../test-utils/auth-test-utils';
import { setMockAuthState, resetMockAuthState } from '../__mocks__/AuthGuard';
import { adminService } from '../../services/admin';

// Mock the services
jest.mock('../../services/admin');

const mockedAdminService = adminService as jest.Mocked<typeof adminService>;

describe('AdminPanel Component', () => {
  const mockUsers = [
    {
      id: 'user-1',
      name: 'John Doe',
      email: 'john@example.com',
      role: 'EMPLOYEE',
      account_status: 'ACTIVE',
      created_at: '2024-01-01T00:00:00Z',
      last_login: '2024-01-15T12:00:00Z'
    },
    {
      id: 'user-2',
      name: 'Jane Smith',
      email: 'jane@example.com',
      role: 'EMPLOYEE',
      account_status: 'SUSPENDED',
      created_at: '2024-01-02T00:00:00Z',
      last_login: '2024-01-14T10:00:00Z'
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    resetMockAuthState();
    
    // Set admin authenticated state
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockAdminUser,
      error: null
    });

    // Setup service mocks
    mockedAdminService.getUsers.mockResolvedValue({
      users: mockUsers,
      pagination: {
        page: 1,
        limit: 10,
        total: 2,
        total_pages: 1
      }
    });

    mockedAdminService.getSystemStats.mockResolvedValue({
      total_users: 150,
      active_users: 140,
      suspended_users: 10,
      total_transactions: 1250,
      total_volume: '125000.00',
      active_events: 5
    });
  });

  it('renders admin panel with system statistics', async () => {
    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Admin Panel')).toBeInTheDocument();
      expect(screen.getByText('System administration and user management')).toBeInTheDocument();
    });

    // Check system statistics
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // Total users
      expect(screen.getByText('140')).toBeInTheDocument(); // Active users
      expect(screen.getByText('10')).toBeInTheDocument(); // Suspended users
      expect(screen.getByText('1,250')).toBeInTheDocument(); // Total transactions
      expect(screen.getByText('£125,000.00')).toBeInTheDocument(); // Total volume
      expect(screen.getByText('5')).toBeInTheDocument(); // Active events
    });
  });

  it('displays user list with management actions', async () => {
    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    // Check user list
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    expect(screen.getByText('jane@example.com')).toBeInTheDocument();

    // Check status badges
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    expect(screen.getByText('SUSPENDED')).toBeInTheDocument();

    // Check action buttons
    expect(screen.getAllByText('Edit')).toHaveLength(2);
    expect(screen.getByText('Suspend')).toBeInTheDocument(); // For active user
    expect(screen.getByText('Activate')).toBeInTheDocument(); // For suspended user
  });

  it('allows searching and filtering users', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    // Search for users
    const searchInput = screen.getByPlaceholderText(/search users/i);
    await user.type(searchInput, 'John');

    await waitFor(() => {
      expect(mockedAdminService.getUsers).toHaveBeenCalledWith({
        search: 'John',
        page: 1,
        limit: 10
      });
    });

    // Filter by status
    const statusFilter = screen.getByLabelText(/filter by status/i);
    await user.selectOptions(statusFilter, 'ACTIVE');

    await waitFor(() => {
      expect(mockedAdminService.getUsers).toHaveBeenCalledWith({
        search: 'John',
        status: 'ACTIVE',
        page: 1,
        limit: 10
      });
    });

    // Filter by role
    const roleFilter = screen.getByLabelText(/filter by role/i);
    await user.selectOptions(roleFilter, 'EMPLOYEE');

    await waitFor(() => {
      expect(mockedAdminService.getUsers).toHaveBeenCalledWith({
        search: 'John',
        status: 'ACTIVE',
        role: 'EMPLOYEE',
        page: 1,
        limit: 10
      });
    });
  });

  it('allows suspending a user', async () => {
    const user = userEvent.setup();

    mockedAdminService.updateUserStatus.mockResolvedValue({
      success: true,
      message: 'User suspended successfully'
    });

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click suspend button for active user
    const suspendButton = screen.getByText('Suspend');
    await user.click(suspendButton);

    // Should show confirmation dialog
    await waitFor(() => {
      expect(screen.getByText(/are you sure you want to suspend/i)).toBeInTheDocument();
    });

    // Confirm suspension
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(mockedAdminService.updateUserStatus).toHaveBeenCalledWith('user-1', 'SUSPENDED');
    });

    await waitFor(() => {
      expect(screen.getByText('User suspended successfully')).toBeInTheDocument();
    });
  });

  it('allows activating a suspended user', async () => {
    const user = userEvent.setup();

    mockedAdminService.updateUserStatus.mockResolvedValue({
      success: true,
      message: 'User activated successfully'
    });

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    // Click activate button for suspended user
    const activateButton = screen.getByText('Activate');
    await user.click(activateButton);

    await waitFor(() => {
      expect(mockedAdminService.updateUserStatus).toHaveBeenCalledWith('user-2', 'ACTIVE');
    });

    await waitFor(() => {
      expect(screen.getByText('User activated successfully')).toBeInTheDocument();
    });
  });

  it('allows editing user details', async () => {
    const user = userEvent.setup();

    mockedAdminService.updateUser.mockResolvedValue({
      success: true,
      message: 'User updated successfully'
    });

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click edit button
    const editButtons = screen.getAllByText('Edit');
    await user.click(editButtons[0]);

    // Should show edit modal
    await waitFor(() => {
      expect(screen.getByText('Edit User')).toBeInTheDocument();
      expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument();
      expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument();
    });

    // Update user details
    const nameInput = screen.getByDisplayValue('John Doe');
    await user.clear(nameInput);
    await user.type(nameInput, 'John Updated');

    const roleSelect = screen.getByDisplayValue('EMPLOYEE');
    await user.selectOptions(roleSelect, 'ADMIN');

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockedAdminService.updateUser).toHaveBeenCalledWith('user-1', {
        name: 'John Updated',
        email: 'john@example.com',
        role: 'ADMIN'
      });
    });

    await waitFor(() => {
      expect(screen.getByText('User updated successfully')).toBeInTheDocument();
    });
  });

  it('shows system configuration section', async () => {
    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('System Configuration')).toBeInTheDocument();
      expect(screen.getByText('Transaction Limits')).toBeInTheDocument();
      expect(screen.getByText('System Maintenance')).toBeInTheDocument();
      expect(screen.getByText('Backup Management')).toBeInTheDocument();
    });
  });

  it('allows updating transaction limits', async () => {
    const user = userEvent.setup();

    mockedAdminService.updateSystemConfig.mockResolvedValue({
      success: true,
      message: 'Configuration updated successfully'
    });

    mockedAdminService.getSystemConfig.mockResolvedValue({
      transaction_limits: {
        max_transaction_amount: '10000.00',
        daily_transaction_limit: '50000.00',
        account_balance_limit: '250.00'
      },
      system_settings: {
        maintenance_mode: false,
        registration_enabled: true
      }
    });

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Transaction Limits')).toBeInTheDocument();
    });

    // Update transaction limits
    const maxTransactionInput = screen.getByLabelText(/max transaction amount/i);
    await user.clear(maxTransactionInput);
    await user.type(maxTransactionInput, '15000');

    const saveConfigButton = screen.getByRole('button', { name: /save configuration/i });
    await user.click(saveConfigButton);

    await waitFor(() => {
      expect(mockedAdminService.updateSystemConfig).toHaveBeenCalledWith({
        transaction_limits: {
          max_transaction_amount: '15000',
          daily_transaction_limit: '50000.00',
          account_balance_limit: '250.00'
        }
      });
    });
  });

  it('allows toggling maintenance mode', async () => {
    const user = userEvent.setup();

    mockedAdminService.toggleMaintenanceMode.mockResolvedValue({
      success: true,
      message: 'Maintenance mode enabled'
    });

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('System Maintenance')).toBeInTheDocument();
    });

    // Toggle maintenance mode
    const maintenanceToggle = screen.getByLabelText(/maintenance mode/i);
    await user.click(maintenanceToggle);

    await waitFor(() => {
      expect(mockedAdminService.toggleMaintenanceMode).toHaveBeenCalledWith(true);
    });

    await waitFor(() => {
      expect(screen.getByText('Maintenance mode enabled')).toBeInTheDocument();
    });
  });

  it('shows audit log section', async () => {
    mockedAdminService.getAuditLogs.mockResolvedValue({
      logs: [
        {
          id: 'log-1',
          user_id: 'user-1',
          user_name: 'John Doe',
          action: 'USER_LOGIN',
          details: 'User logged in successfully',
          ip_address: '192.168.1.1',
          created_at: '2024-01-15T12:00:00Z'
        }
      ],
      pagination: {
        page: 1,
        limit: 10,
        total: 1,
        total_pages: 1
      }
    });

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Audit Logs')).toBeInTheDocument();
    });

    // Check audit log entries
    await waitFor(() => {
      expect(screen.getByText('USER_LOGIN')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('User logged in successfully')).toBeInTheDocument();
      expect(screen.getByText('192.168.1.1')).toBeInTheDocument();
    });
  });

  it('handles pagination for user list', async () => {
    const user = userEvent.setup();

    // Mock response with multiple pages
    mockedAdminService.getUsers.mockResolvedValue({
      users: mockUsers,
      pagination: {
        page: 1,
        limit: 10,
        total: 25,
        total_pages: 3
      }
    });

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument();
    });

    // Check pagination controls
    expect(screen.getByText(/page 1 of 3/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next page/i })).toBeInTheDocument();

    // Click next page
    const nextButton = screen.getByRole('button', { name: /next page/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(mockedAdminService.getUsers).toHaveBeenCalledWith({
        page: 2,
        limit: 10
      });
    });
  });

  it('shows loading state during data fetch', async () => {
    // Mock delayed response
    mockedAdminService.getUsers.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        users: mockUsers,
        pagination: {
          page: 1,
          limit: 10,
          total: 2,
          total_pages: 1
        }
      }), 100))
    );

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    expect(screen.getByText(/loading admin panel/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Admin Panel')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    mockedAdminService.getUsers.mockRejectedValue(new Error('Failed to load users'));
    mockedAdminService.getSystemStats.mockRejectedValue(new Error('Failed to load stats'));

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load users')).toBeInTheDocument();
      expect(screen.getByText('Failed to load stats')).toBeInTheDocument();
    });
  });

  it('restricts access to admin users only', async () => {
    // Set non-admin user
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: { ...mockAdminUser, role: 'EMPLOYEE' },
      error: null
    });

    render(
      <TestWrapper>
        <AdminPanel />
      </TestWrapper>
    );

    // Should show access denied message
    await waitFor(() => {
      expect(screen.getByText(/access denied/i)).toBeInTheDocument();
      expect(screen.getByText(/admin privileges required/i)).toBeInTheDocument();
    });
  });
});