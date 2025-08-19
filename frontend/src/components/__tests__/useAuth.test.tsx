import { renderHook, act } from '@testing-library/react';
import { useAuth } from '../AuthGuard';
import { setMockAuthState, resetMockAuthState } from '../__mocks__/AuthGuard';
import { mockUser, mockAdminUser, mockFinanceUser } from '../../test-utils/auth-test-utils';

describe('useAuth Hook', () => {
  beforeEach(() => {
    resetMockAuthState();
  });

  it('returns default authenticated state', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.isInitialized).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.error).toBeNull();
  });

  it('returns loading state', () => {
    setMockAuthState({
      isAuthenticated: false,
      isInitialized: false,
      isLoading: true,
      user: null,
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isInitialized).toBe(false);
    expect(result.current.isLoading).toBe(true);
    expect(result.current.user).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('returns unauthenticated state', () => {
    setMockAuthState({
      isAuthenticated: false,
      isInitialized: true,
      isLoading: false,
      user: null,
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isInitialized).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('returns error state', () => {
    setMockAuthState({
      isAuthenticated: false,
      isInitialized: true,
      isLoading: false,
      user: null,
      error: 'Authentication failed'
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.error).toBe('Authentication failed');
  });

  it('provides role checking functions', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockAdminUser,
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.hasRole).toBeDefined();
    expect(result.current.hasAnyRole).toBeDefined();
    expect(result.current.isAdmin).toBeDefined();
    expect(result.current.isFinance).toBeDefined();

    // Test role checking
    expect(result.current.hasRole('ADMIN')).toBe(true);
    expect(result.current.hasRole('EMPLOYEE')).toBe(false);
    expect(result.current.isAdmin()).toBe(true);
    expect(result.current.isFinance()).toBe(false);
  });

  it('provides permission checking functions', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: { ...mockUser, permissions: ['read', 'write', 'admin'] },
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.hasPermission).toBeDefined();
    expect(result.current.hasAnyPermission).toBeDefined();
    expect(result.current.hasAllPermissions).toBeDefined();

    // Test permission checking
    expect(result.current.hasPermission('read')).toBe(true);
    expect(result.current.hasPermission('delete')).toBe(false);
    expect(result.current.hasAnyPermission(['read', 'delete'])).toBe(true);
    expect(result.current.hasAllPermissions(['read', 'write'])).toBe(true);
    expect(result.current.hasAllPermissions(['read', 'delete'])).toBe(false);
  });

  it('provides authentication action functions', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.login).toBeDefined();
    expect(result.current.logout).toBeDefined();
    expect(result.current.refreshToken).toBeDefined();
    expect(result.current.updatePermissions).toBeDefined();

    expect(typeof result.current.login).toBe('function');
    expect(typeof result.current.logout).toBe('function');
    expect(typeof result.current.refreshToken).toBe('function');
    expect(typeof result.current.updatePermissions).toBe('function');
  });

  it('handles role checking for different user types', () => {
    // Test employee user
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    });

    let { result } = renderHook(() => useAuth());
    expect(result.current.hasRole('EMPLOYEE')).toBe(true);
    expect(result.current.isAdmin()).toBe(false);
    expect(result.current.isFinance()).toBe(false);

    // Test admin user
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockAdminUser,
      error: null
    });

    ({ result } = renderHook(() => useAuth()));
    expect(result.current.hasRole('ADMIN')).toBe(true);
    expect(result.current.isAdmin()).toBe(true);
    expect(result.current.isFinance()).toBe(false);

    // Test finance user
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockFinanceUser,
      error: null
    });

    ({ result } = renderHook(() => useAuth()));
    expect(result.current.hasRole('FINANCE')).toBe(true);
    expect(result.current.isAdmin()).toBe(false);
    expect(result.current.isFinance()).toBe(true);
  });

  it('handles null user gracefully', () => {
    setMockAuthState({
      isAuthenticated: false,
      isInitialized: true,
      isLoading: false,
      user: null,
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.hasRole('EMPLOYEE')).toBe(false);
    expect(result.current.hasPermission('read')).toBe(false);
    expect(result.current.isAdmin()).toBe(false);
    expect(result.current.isFinance()).toBe(false);
  });

  it('handles user without permissions gracefully', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: { ...mockUser, permissions: undefined },
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.hasPermission('read')).toBe(false);
    expect(result.current.hasAnyPermission(['read', 'write'])).toBe(false);
    expect(result.current.hasAllPermissions(['read', 'write'])).toBe(false);
  });

  it('updates state when mock state changes', () => {
    setMockAuthState({
      isAuthenticated: false,
      isInitialized: true,
      isLoading: false,
      user: null,
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();

    // Update mock state
    act(() => {
      setMockAuthState({
        isAuthenticated: true,
        isInitialized: true,
        isLoading: false,
        user: mockUser,
        error: null
      });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual(mockUser);
  });

  it('provides consistent function references', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    });

    const { result, rerender } = renderHook(() => useAuth());

    const initialLogin = result.current.login;
    const initialLogout = result.current.logout;
    const initialHasRole = result.current.hasRole;

    rerender();

    // Functions should maintain reference equality to prevent unnecessary re-renders
    expect(result.current.login).toBe(initialLogin);
    expect(result.current.logout).toBe(initialLogout);
    expect(result.current.hasRole).toBe(initialHasRole);
  });

  it('handles multiple role checking', () => {
    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockAdminUser,
      error: null
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.hasAnyRole(['EMPLOYEE', 'ADMIN'])).toBe(true);
    expect(result.current.hasAnyRole(['EMPLOYEE', 'FINANCE'])).toBe(false);
  });

  it('does not cause infinite re-renders', () => {
    let renderCount = 0;

    setMockAuthState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      user: mockUser,
      error: null
    });

    const { result } = renderHook(() => {
      renderCount++;
      return useAuth();
    });

    expect(renderCount).toBe(1);
    expect(result.current.user).toEqual(mockUser);

    // Multiple accesses shouldn't cause re-renders
    const user1 = result.current.user;
    const user2 = result.current.user;
    const isAuth1 = result.current.isAuthenticated;
    const isAuth2 = result.current.isAuthenticated;

    expect(renderCount).toBe(1);
    expect(user1).toBe(user2);
    expect(isAuth1).toBe(isAuth2);
  });
});