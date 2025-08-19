import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock Microsoft SSO endpoints
    await page.route('**/api/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          user: {
            id: '1',
            name: 'Test User',
            email: 'test@company.com',
            role: 'employee'
          }
        })
      });
    });

    await page.route('**/api/accounts/balance', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          balance: '150.00',
          currency: 'GBP'
        })
      });
    });
  });

  test('should redirect unauthenticated user to login', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Should redirect to login page
    await expect(page).toHaveURL('/login');
    await expect(page.locator('h1')).toContainText('Sign In');
  });

  test('should complete Microsoft SSO login flow', async ({ page }) => {
    await page.goto('/login');

    // Click Microsoft SSO button
    await page.click('button:has-text("Sign in with Microsoft")');

    // Mock Microsoft OAuth redirect
    await page.route('**/oauth2/v2.0/authorize**', async route => {
      // Simulate successful OAuth callback
      await page.goto('/auth/callback?code=mock-auth-code&state=mock-state');
    });

    // Should redirect to dashboard after successful login
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('[data-testid="user-name"]')).toContainText('Test User');
  });

  test('should handle login error gracefully', async ({ page }) => {
    // Mock login failure
    await page.route('**/api/auth/login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid authentication credentials'
          }
        })
      });
    });

    await page.goto('/auth/callback?code=invalid-code');

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid authentication credentials');
    
    // Should stay on login page
    await expect(page).toHaveURL('/login');
  });

  test('should logout user and clear session', async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'mock-token');
      localStorage.setItem('refresh_token', 'mock-refresh-token');
    });

    await page.goto('/dashboard');

    // Click logout button
    await page.click('[data-testid="logout-button"]');

    // Should redirect to login
    await expect(page).toHaveURL('/login');

    // Should clear tokens
    const accessToken = await page.evaluate(() => localStorage.getItem('access_token'));
    const refreshToken = await page.evaluate(() => localStorage.getItem('refresh_token'));
    
    expect(accessToken).toBeNull();
    expect(refreshToken).toBeNull();
  });

  test('should refresh token automatically when expired', async ({ page }) => {
    // Mock token refresh endpoint
    await page.route('**/api/auth/refresh', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token'
        })
      });
    });

    // Mock expired token response
    await page.route('**/api/accounts/balance', async route => {
      const authHeader = route.request().headers()['authorization'];
      if (authHeader === 'Bearer expired-token') {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: { code: 'TOKEN_EXPIRED', message: 'Token expired' }
          })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            balance: '150.00',
            currency: 'GBP'
          })
        });
      }
    });

    // Set expired token
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('refresh_token', 'valid-refresh-token');
    });

    await page.goto('/dashboard');

    // Should automatically refresh token and load dashboard
    await expect(page.locator('[data-testid="balance"]')).toContainText('£150.00');

    // Should update token in localStorage
    const newToken = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(newToken).toBe('new-access-token');
  });

  test('should handle session timeout', async ({ page }) => {
    // Mock session timeout
    await page.route('**/api/auth/refresh', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: { code: 'REFRESH_TOKEN_EXPIRED', message: 'Refresh token expired' }
        })
      });
    });

    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('refresh_token', 'expired-refresh-token');
    });

    await page.goto('/dashboard');

    // Should redirect to login after failed refresh
    await expect(page).toHaveURL('/login');
    await expect(page.locator('[data-testid="session-expired-message"]')).toContainText('Your session has expired');
  });
});