/**
 * End-to-end tests for complete user workflows
 * Tests the entire application from login to transaction completion
 */
import { test, expect, Page } from '@playwright/test'

// Mock user data
const mockUser = {
  id: '1',
  email: 'test@softbank.com',
  name: 'Test User',
  role: 'EMPLOYEE'
}

const mockAdminUser = {
  id: '2',
  email: 'admin@softbank.com',
  name: 'Admin User',
  role: 'ADMIN'
}

// Helper function to mock authentication
async function mockAuthentication(page: Page, user = mockUser) {
  await page.route('**/api/auth/**', async (route) => {
    const url = route.request().url()
    
    if (url.includes('/auth/me')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ user })
      })
    } else if (url.includes('/auth/login')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-token',
          refresh_token: 'mock-refresh-token',
          user
        })
      })
    } else {
      await route.continue()
    }
  })

  // Mock account data
  await page.route('**/api/accounts/**', async (route) => {
    const url = route.request().url()
    
    if (url.includes('/balance')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          balance: '150.00',
          available_balance: '100.00',
          currency: 'GBP'
        })
      })
    } else if (url.includes('/analytics')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_spent: '75.00',
          total_received: '100.00'
        })
      })
    } else {
      await route.continue()
    }
  })

  // Mock transaction data
  await page.route('**/api/transactions/**', async (route) => {
    const url = route.request().url()
    
    if (url.includes('/recent')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
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
          ]
        })
      })
    } else if (url.includes('/send')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          transaction: {
            id: '2',
            sender_id: '1',
            recipient_id: '3',
            amount: '50.00',
            status: 'COMPLETED'
          }
        })
      })
    } else {
      await route.continue()
    }
  })

  // Mock events data
  await page.route('**/api/events/**', async (route) => {
    const url = route.request().url()
    
    if (url.includes('/active')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
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
        })
      })
    } else {
      await route.continue()
    }
  })

  // Mock money requests data
  await page.route('**/api/money-requests/**', async (route) => {
    const url = route.request().url()
    
    if (url.includes('/pending')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
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
        })
      })
    } else {
      await route.continue()
    }
  })

  // Set authentication tokens in localStorage
  await page.addInitScript(() => {
    localStorage.setItem('access_token', 'mock-token')
    localStorage.setItem('refresh_token', 'mock-refresh-token')
    localStorage.setItem('user', JSON.stringify(mockUser))
  })
}

test.describe('Complete User Workflows', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthentication(page)
  })

  test('complete dashboard workflow', async ({ page }) => {
    await page.goto('/')

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard')

    // Check dashboard loads correctly
    await expect(page.getByText('Welcome back, Test!')).toBeVisible()
    await expect(page.getByText('£150.00')).toBeVisible()
    await expect(page.getByText('Available: £100.00')).toBeVisible()

    // Check quick actions are present
    await expect(page.getByText('Send Money')).toBeVisible()
    await expect(page.getByText('Request Money')).toBeVisible()
    await expect(page.getByText('View Events')).toBeVisible()
    await expect(page.getByText('View Reports')).toBeVisible()

    // Check recent transactions
    await expect(page.getByText('Recent Transactions')).toBeVisible()
    await expect(page.getByText('To John Doe')).toBeVisible()
    await expect(page.getByText('-£25.00')).toBeVisible()

    // Check stats
    await expect(page.getByText('This Month Received')).toBeVisible()
    await expect(page.getByText('This Month Spent')).toBeVisible()
    await expect(page.getByText('Pending Requests')).toBeVisible()
  })

  test('send money workflow', async ({ page }) => {
    await page.goto('/dashboard')

    // Click send money button
    await page.getByText('Send Money').click()
    await expect(page).toHaveURL('/transactions/send')

    // Fill out send money form
    await page.fill('[data-testid="recipient-search"]', 'john@softbank.com')
    await page.fill('[data-testid="amount-input"]', '50.00')
    await page.fill('[data-testid="note-input"]', 'Test payment')

    // Submit form
    await page.click('[data-testid="send-button"]')

    // Check success message
    await expect(page.getByText('Money sent successfully')).toBeVisible()
  })

  test('navigation workflow', async ({ page }) => {
    await page.goto('/dashboard')

    // Test navigation to different pages
    await page.getByText('View Events').click()
    await expect(page).toHaveURL('/events/active')

    // Navigate back to dashboard
    await page.getByText('SoftBankCashWire').click()
    await expect(page).toHaveURL('/dashboard')

    // Test transaction history navigation
    await page.getByText('View all').first().click()
    await expect(page).toHaveURL('/transactions/history')
  })

  test('accessibility features workflow', async ({ page }) => {
    await page.goto('/dashboard')

    // Test skip to main content
    await page.keyboard.press('Tab')
    await expect(page.getByText('Skip to main content')).toBeFocused()
    await page.keyboard.press('Enter')
    await expect(page.locator('#main-content')).toBeFocused()

    // Test accessibility settings
    await page.getByLabelText('Open accessibility settings').click()
    await expect(page.getByText('Accessibility Settings')).toBeVisible()

    // Test high contrast mode
    await page.getByText('High Contrast').click()
    await expect(page.locator('body')).toHaveClass(/high-contrast/)

    // Close accessibility settings
    await page.getByText('Close').click()
    await expect(page.getByText('Accessibility Settings')).not.toBeVisible()
  })

  test('notification workflow', async ({ page }) => {
    await page.goto('/dashboard')

    // Open notification center
    await page.getByLabelText(/notifications/i).click()
    await expect(page.getByText('Notifications')).toBeVisible()

    // Check notification content
    await expect(page.getByText('No new notifications')).toBeVisible()

    // Close notification center
    await page.keyboard.press('Escape')
    await expect(page.getByText('Notifications')).not.toBeVisible()
  })

  test('logout workflow', async ({ page }) => {
    await page.goto('/dashboard')

    // Click logout
    await page.getByText('Logout').click()

    // Should redirect to login page
    await expect(page).toHaveURL('/login')
    await expect(page.getByText('Sign in to SoftBankCashWire')).toBeVisible()
  })

  test('error handling workflow', async ({ page }) => {
    // Mock API error
    await page.route('**/api/accounts/balance', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'INTERNAL_ERROR',
            message: 'Internal server error'
          }
        })
      })
    })

    await page.goto('/dashboard')

    // Check error message is displayed
    await expect(page.getByText('Error Loading Dashboard')).toBeVisible()
    await expect(page.getByText('Internal server error')).toBeVisible()

    // Test retry functionality
    await page.getByText('Retry').click()
  })

  test('responsive design workflow', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/dashboard')

    // Check mobile layout
    await expect(page.getByText('Welcome back, Test!')).toBeVisible()
    await expect(page.getByText('Send Money')).toBeVisible()

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 })
    await expect(page.getByText('Welcome back, Test!')).toBeVisible()

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 })
    await expect(page.getByText('Welcome back, Test!')).toBeVisible()
  })
})

test.describe('Admin User Workflows', () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthentication(page, mockAdminUser)
  })

  test('admin panel access workflow', async ({ page }) => {
    await page.goto('/admin')

    // Should have access to admin panel
    await expect(page.getByText('Admin Panel')).toBeVisible()
    await expect(page.getByText('User Management')).toBeVisible()
  })

  test('admin reports access workflow', async ({ page }) => {
    await page.goto('/reports/admin')

    // Should have access to admin reports
    await expect(page.getByText('Administrative Reports')).toBeVisible()
  })
})

test.describe('Role-Based Access Control', () => {
  test('regular user cannot access admin routes', async ({ page }) => {
    await mockAuthentication(page, mockUser)
    await page.goto('/admin')

    // Should be redirected to unauthorized page
    await expect(page.getByText('Access Denied')).toBeVisible()
    await expect(page.getByText("You don't have permission to access this page.")).toBeVisible()
  })

  test('unauthenticated user redirected to login', async ({ page }) => {
    // Don't mock authentication
    await page.goto('/dashboard')

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/)
    await expect(page.getByText('Sign in to SoftBankCashWire')).toBeVisible()
  })
})

test.describe('Performance and Load Testing', () => {
  test('dashboard loads within performance budget', async ({ page }) => {
    await mockAuthentication(page)
    
    const startTime = Date.now()
    await page.goto('/dashboard')
    await expect(page.getByText('Welcome back, Test!')).toBeVisible()
    const loadTime = Date.now() - startTime

    // Should load within 2 seconds
    expect(loadTime).toBeLessThan(2000)
  })

  test('handles multiple rapid navigation', async ({ page }) => {
    await mockAuthentication(page)
    await page.goto('/dashboard')

    // Rapidly navigate between pages
    for (let i = 0; i < 5; i++) {
      await page.getByText('Send Money').click()
      await expect(page).toHaveURL('/transactions/send')
      
      await page.getByText('SoftBankCashWire').click()
      await expect(page).toHaveURL('/dashboard')
    }

    // Should still be functional
    await expect(page.getByText('Welcome back, Test!')).toBeVisible()
  })
})

test.describe('Security Testing', () => {
  test('prevents XSS in user input', async ({ page }) => {
    await mockAuthentication(page)
    await page.goto('/transactions/send')

    // Try to inject script
    await page.fill('[data-testid="note-input"]', '<script>alert("xss")</script>')
    
    // Script should be escaped/sanitized
    const noteValue = await page.inputValue('[data-testid="note-input"]')
    expect(noteValue).not.toContain('<script>')
  })

  test('validates authentication tokens', async ({ page }) => {
    await page.goto('/dashboard')

    // Remove auth token
    await page.evaluate(() => {
      localStorage.removeItem('access_token')
    })

    // Refresh page
    await page.reload()

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/)
  })
})