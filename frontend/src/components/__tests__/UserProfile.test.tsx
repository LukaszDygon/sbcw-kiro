import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UserProfile from '../UserProfile';
import { TestWrapper, mockUser } from '../../test-utils/auth-test-utils';
import { setMockAuthState, resetMockAuthState } from '../__mocks__/AuthGuard';
import { accountsService } from '../../services/accounts';
import { authService } from '../../services/auth';

// Mock the services
jest.mock('../../services/accounts');
jest.mock('../../services/auth');

const mockedAccountsService = accountsService as jest.Mocked<typeof accountsService>;
const mockedAuthService = authService as jest.Mocked<typeof authService>;

describe('UserProfile Component', () => {
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
    mockedAccountsService.getProfile.mockResolvedValue({
      id: mockUser.id,
      name: mockUser.name,
      email: mockUser.email,
      role: mockUser.role,
      account_status: 'ACTIVE',
      created_at: '2024-01-01T00:00:00Z',
      last_login: '2024-01-15T12:00:00Z',
      preferences: {
        notifications_enabled: true,
        email_notifications: true,
        theme: 'light'
      }
    });

    mockedAccountsService.updateProfile.mockResolvedValue({
      success: true,
      message: 'Profile updated successfully'
    });
  });

  it('renders user profile information', async () => {
    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
      expect(screen.getByText('Manage your account settings and preferences')).toBeInTheDocument();
    });

    // Check profile information
    expect(screen.getByDisplayValue(mockUser.name)).toBeInTheDocument();
    expect(screen.getByDisplayValue(mockUser.email)).toBeInTheDocument();
    expect(screen.getByText(mockUser.role)).toBeInTheDocument();
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });

  it('displays account statistics', async () => {
    mockedAccountsService.getAccountStats.mockResolvedValue({
      total_transactions: 25,
      total_sent: '500.00',
      total_received: '750.00',
      events_participated: 5,
      account_age_days: 365
    });

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('25')).toBeInTheDocument(); // Total transactions
      expect(screen.getByText('£500.00')).toBeInTheDocument(); // Total sent
      expect(screen.getByText('£750.00')).toBeInTheDocument(); // Total received
      expect(screen.getByText('5')).toBeInTheDocument(); // Events participated
    });
  });

  it('allows updating profile preferences', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });

    // Toggle notification preferences
    const notificationsToggle = screen.getByLabelText(/enable notifications/i);
    await user.click(notificationsToggle);

    const emailNotificationsToggle = screen.getByLabelText(/email notifications/i);
    await user.click(emailNotificationsToggle);

    // Change theme
    const themeSelect = screen.getByLabelText(/theme/i);
    await user.selectOptions(themeSelect, 'dark');

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockedAccountsService.updateProfile).toHaveBeenCalledWith({
        preferences: {
          notifications_enabled: false,
          email_notifications: false,
          theme: 'dark'
        }
      });
    });

    // Should show success message
    await waitFor(() => {
      expect(screen.getByText('Profile updated successfully')).toBeInTheDocument();
    });
  });

  it('validates name input', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue(mockUser.name);
    
    // Clear name (should be required)
    await user.clear(nameInput);
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
    });

    // Test name too short
    await user.type(nameInput, 'ab');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Name must be at least 3 characters')).toBeInTheDocument();
    });

    // Test name too long
    await user.clear(nameInput);
    const longName = 'a'.repeat(101);
    await user.type(nameInput, longName);
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Name cannot exceed 100 characters')).toBeInTheDocument();
    });
  });

  it('shows loading state during profile update', async () => {
    const user = userEvent.setup();

    // Mock delayed response
    mockedAccountsService.updateProfile.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        success: true,
        message: 'Profile updated successfully'
      }), 100))
    );

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(saveButton);

    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText(/saving/i)).toBeInTheDocument();
    });

    expect(saveButton).toBeDisabled();
  });

  it('handles profile update errors', async () => {
    const user = userEvent.setup();

    mockedAccountsService.updateProfile.mockRejectedValue(new Error('Update failed'));

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Update failed')).toBeInTheDocument();
    });
  });

  it('displays security section with password change', async () => {
    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Security')).toBeInTheDocument();
      expect(screen.getByText('Change Password')).toBeInTheDocument();
      expect(screen.getByText('Last Login')).toBeInTheDocument();
    });

    // Should show formatted last login date
    expect(screen.getByText(/Jan 15, 2024/)).toBeInTheDocument();
  });

  it('allows changing password', async () => {
    const user = userEvent.setup();

    mockedAuthService.changePassword.mockResolvedValue({
      success: true,
      message: 'Password changed successfully'
    });

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });

    // Click change password button
    const changePasswordButton = screen.getByRole('button', { name: /change password/i });
    await user.click(changePasswordButton);

    // Should show password change form
    await waitFor(() => {
      expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    });

    // Fill in password form
    const currentPasswordInput = screen.getByLabelText(/current password/i);
    const newPasswordInput = screen.getByLabelText(/new password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

    await user.type(currentPasswordInput, 'currentpass');
    await user.type(newPasswordInput, 'newpassword123');
    await user.type(confirmPasswordInput, 'newpassword123');

    // Submit password change
    const submitPasswordButton = screen.getByRole('button', { name: /update password/i });
    await user.click(submitPasswordButton);

    await waitFor(() => {
      expect(mockedAuthService.changePassword).toHaveBeenCalledWith({
        current_password: 'currentpass',
        new_password: 'newpassword123'
      });
    });

    await waitFor(() => {
      expect(screen.getByText('Password changed successfully')).toBeInTheDocument();
    });
  });

  it('validates password change form', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });

    // Click change password button
    const changePasswordButton = screen.getByRole('button', { name: /change password/i });
    await user.click(changePasswordButton);

    await waitFor(() => {
      expect(screen.getByLabelText(/current password/i)).toBeInTheDocument();
    });

    // Try to submit without filling fields
    const submitPasswordButton = screen.getByRole('button', { name: /update password/i });
    await user.click(submitPasswordButton);

    await waitFor(() => {
      expect(screen.getByText('Current password is required')).toBeInTheDocument();
      expect(screen.getByText('New password is required')).toBeInTheDocument();
    });

    // Test password mismatch
    const newPasswordInput = screen.getByLabelText(/new password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

    await user.type(newPasswordInput, 'password1');
    await user.type(confirmPasswordInput, 'password2');
    await user.click(submitPasswordButton);

    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    });
  });

  it('shows account deletion section for appropriate users', async () => {
    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Danger Zone')).toBeInTheDocument();
      expect(screen.getByText('Delete Account')).toBeInTheDocument();
      expect(screen.getByText(/this action cannot be undone/i)).toBeInTheDocument();
    });
  });

  it('handles account deletion with confirmation', async () => {
    const user = userEvent.setup();

    mockedAccountsService.deleteAccount.mockResolvedValue({
      success: true,
      message: 'Account deleted successfully'
    });

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    await user.click(deleteButton);

    expect(confirmSpy).toHaveBeenCalledWith(
      'Are you sure you want to delete your account? This action cannot be undone.'
    );

    await waitFor(() => {
      expect(mockedAccountsService.deleteAccount).toHaveBeenCalled();
    });

    confirmSpy.mockRestore();
  });

  it('cancels account deletion when not confirmed', async () => {
    const user = userEvent.setup();

    // Mock window.confirm to return false
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: /delete account/i });
    await user.click(deleteButton);

    expect(confirmSpy).toHaveBeenCalled();
    expect(mockedAccountsService.deleteAccount).not.toHaveBeenCalled();

    confirmSpy.mockRestore();
  });

  it('shows loading state during initial data fetch', async () => {
    // Mock delayed response
    mockedAccountsService.getProfile.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        id: mockUser.id,
        name: mockUser.name,
        email: mockUser.email,
        role: mockUser.role,
        account_status: 'ACTIVE',
        created_at: '2024-01-01T00:00:00Z',
        last_login: '2024-01-15T12:00:00Z',
        preferences: {
          notifications_enabled: true,
          email_notifications: true,
          theme: 'light'
        }
      }), 100))
    );

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    expect(screen.getByText(/loading profile/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('User Profile')).toBeInTheDocument();
    });
  });

  it('handles profile fetch errors', async () => {
    mockedAccountsService.getProfile.mockRejectedValue(new Error('Failed to load profile'));

    render(
      <TestWrapper>
        <UserProfile />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load profile')).toBeInTheDocument();
    });
  });
});