import { test, expect } from '@playwright/test';

test.describe('Money Transfer Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.addInitScript(() => {
      localStorage.setItem('access_token', 'mock-token');
      localStorage.setItem('user', JSON.stringify({
        id: '1',
        name: 'Test User',
        email: 'test@company.com',
        role: 'employee'
      }));
    });

    // Mock API endpoints
    await page.route('**/api/accounts/balance', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          balance: '200.00',
          currency: 'GBP'
        })
      });
    });

    await page.route('**/api/accounts/search**', async route => {
      const url = new URL(route.request().url());
      const query = url.searchParams.get('q');
      
      const users = [
        { id: '2', name: 'John Doe', email: 'john@company.com' },
        { id: '3', name: 'Jane Smith', email: 'jane@company.com' },
        { id: '4', name: 'Bob Johnson', email: 'bob@company.com' }
      ];

      const filteredUsers = users.filter(user => 
        user.name.toLowerCase().includes(query?.toLowerCase() || '') ||
        user.email.toLowerCase().includes(query?.toLowerCase() || '')
      );

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(filteredUsers)
      });
    });
  });

  test('should complete successful money transfer', async ({ page }) => {
    // Mock successful transfer
    await page.route('**/api/transactions/send', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          transaction: {
            id: 'trans-123',
            amount: '25.00',
            recipient_name: 'John Doe',
            sender_name: 'Test User',
            note: 'Lunch payment',
            created_at: '2024-01-15T12:00:00Z'
          },
          sender_balance: '175.00',
          recipient_balance: '125.00'
        })
      });
    });

    await page.goto('/send');

    // Fill recipient field
    await page.fill('[data-testid="recipient-input"]', 'John');
    
    // Wait for search results and select recipient
    await expect(page.locator('[data-testid="user-search-result"]')).toContainText('John Doe');
    await page.click('[data-testid="user-search-result"]:has-text("John Doe")');

    // Fill amount
    await page.fill('[data-testid="amount-input"]', '25.00');

    // Fill note
    await page.fill('[data-testid="note-input"]', 'Lunch payment');

    // Submit form
    await page.click('[data-testid="send-money-button"]');

    // Should show success message
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Money sent successfully');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
  });

  test('should validate form inputs', async ({ page }) => {
    await page.goto('/send');

    // Try to submit without recipient
    await page.fill('[data-testid="amount-input"]', '25.00');
    await page.click('[data-testid="send-money-button"]');

    await expect(page.locator('[data-testid="recipient-error"]')).toContainText('Please select a recipient');

    // Fill recipient
    await page.fill('[data-testid="recipient-input"]', 'John');
    await page.click('[data-testid="user-search-result"]:has-text("John Doe")');

    // Try negative amount
    await page.fill('[data-testid="amount-input"]', '-10');
    await page.blur('[data-testid="amount-input"]');

    await expect(page.locator('[data-testid="amount-error"]')).toContainText('Amount must be positive');

    // Try zero amount
    await page.fill('[data-testid="amount-input"]', '0');
    await page.blur('[data-testid="amount-input"]');

    await expect(page.locator('[data-testid="amount-error"]')).toContainText('Amount must be greater than zero');

    // Try amount exceeding balance + overdraft
    await page.fill('[data-testid="amount-input"]', '500');
    await page.blur('[data-testid="amount-input"]');

    await expect(page.locator('[data-testid="amount-error"]')).toContainText('Amount exceeds available balance');
  });

  test('should handle insufficient funds error', async ({ page }) => {
    // Mock insufficient funds error
    await page.route('**/api/transactions/send', async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'INSUFFICIENT_FUNDS',
            message: 'Insufficient funds for this transaction',
            details: {
              current_balance: '200.00',
              required_amount: '300.00',
              available_overdraft: '250.00'
            }
          }
        })
      });
    });

    await page.goto('/send');

    // Fill form
    await page.fill('[data-testid="recipient-input"]', 'John');
    await page.click('[data-testid="user-search-result"]:has-text("John Doe")');
    await page.fill('[data-testid="amount-input"]', '300.00');
    await page.click('[data-testid="send-money-button"]');

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Insufficient funds for this transaction');
    
    // Should show balance details
    await expect(page.locator('[data-testid="balance-details"]')).toContainText('Current balance: £200.00');
    await expect(page.locator('[data-testid="balance-details"]')).toContainText('Available overdraft: £250.00');
  });

  test('should support bulk money transfer', async ({ page }) => {
    // Mock bulk transfer
    await page.route('**/api/transactions/send-bulk', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          total_amount: '50.00',
          recipient_count: 2,
          transactions: [
            {
              id: 'trans-1',
              amount: '25.00',
              recipient_name: 'John Doe',
              sender_name: 'Test User',
              note: 'Lunch split',
              created_at: '2024-01-15T12:00:00Z'
            },
            {
              id: 'trans-2',
              amount: '25.00',
              recipient_name: 'Jane Smith',
              sender_name: 'Test User',
              note: 'Lunch split',
              created_at: '2024-01-15T12:00:00Z'
            }
          ],
          sender_balance: '150.00'
        })
      });
    });

    await page.goto('/send');

    // Enable bulk mode
    await page.check('[data-testid="bulk-mode-toggle"]');

    // Add first recipient
    await page.fill('[data-testid="recipient-input-0"]', 'John');
    await page.click('[data-testid="user-search-result"]:has-text("John Doe")');
    await page.fill('[data-testid="amount-input-0"]', '25.00');

    // Add second recipient
    await page.click('[data-testid="add-recipient-button"]');
    await page.fill('[data-testid="recipient-input-1"]', 'Jane');
    await page.click('[data-testid="user-search-result"]:has-text("Jane Smith")');
    await page.fill('[data-testid="amount-input-1"]', '25.00');

    // Fill common note
    await page.fill('[data-testid="bulk-note-input"]', 'Lunch split');

    // Submit bulk transfer
    await page.click('[data-testid="send-bulk-button"]');

    // Should show success message
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Bulk transfer completed successfully');
    await expect(page.locator('[data-testid="success-details"]')).toContainText('Sent £50.00 to 2 recipients');
  });

  test('should show real-time balance updates', async ({ page }) => {
    await page.goto('/send');

    // Initial balance should be displayed
    await expect(page.locator('[data-testid="current-balance"]')).toContainText('£200.00');

    // Enter amount and check remaining balance preview
    await page.fill('[data-testid="amount-input"]', '50.00');
    
    await expect(page.locator('[data-testid="remaining-balance"]')).toContainText('Remaining: £150.00');

    // Test overdraft warning
    await page.fill('[data-testid="amount-input"]', '400.00');
    
    await expect(page.locator('[data-testid="overdraft-warning"]')).toContainText('This will put you £150.00 into overdraft');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Mock network error
    await page.route('**/api/transactions/send', async route => {
      await route.abort('failed');
    });

    await page.goto('/send');

    // Fill form
    await page.fill('[data-testid="recipient-input"]', 'John');
    await page.click('[data-testid="user-search-result"]:has-text("John Doe")');
    await page.fill('[data-testid="amount-input"]', '25.00');
    await page.click('[data-testid="send-money-button"]');

    // Should show network error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Network error. Please try again.');
    
    // Form should remain filled for retry
    await expect(page.locator('[data-testid="amount-input"]')).toHaveValue('25.00');
  });

  test('should prevent sending money to self', async ({ page }) => {
    // Mock search returning current user
    await page.route('**/api/accounts/search**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: '1', name: 'Test User', email: 'test@company.com' }, // Current user
          { id: '2', name: 'John Doe', email: 'john@company.com' }
        ])
      });
    });

    await page.goto('/send');

    // Try to select self as recipient
    await page.fill('[data-testid="recipient-input"]', 'Test User');
    await page.click('[data-testid="user-search-result"]:has-text("Test User")');

    // Should show error
    await expect(page.locator('[data-testid="recipient-error"]')).toContainText('You cannot send money to yourself');
    
    // Send button should be disabled
    await expect(page.locator('[data-testid="send-money-button"]')).toBeDisabled();
  });

  test('should show transaction confirmation dialog', async ({ page }) => {
    await page.goto('/send');

    // Fill form
    await page.fill('[data-testid="recipient-input"]', 'John');
    await page.click('[data-testid="user-search-result"]:has-text("John Doe")');
    await page.fill('[data-testid="amount-input"]', '25.00');
    await page.fill('[data-testid="note-input"]', 'Lunch payment');

    // Click send button
    await page.click('[data-testid="send-money-button"]');

    // Should show confirmation dialog
    await expect(page.locator('[data-testid="confirmation-dialog"]')).toBeVisible();
    await expect(page.locator('[data-testid="confirmation-amount"]')).toContainText('£25.00');
    await expect(page.locator('[data-testid="confirmation-recipient"]')).toContainText('John Doe');
    await expect(page.locator('[data-testid="confirmation-note"]')).toContainText('Lunch payment');

    // Can cancel
    await page.click('[data-testid="cancel-button"]');
    await expect(page.locator('[data-testid="confirmation-dialog"]')).not.toBeVisible();

    // Can confirm
    await page.click('[data-testid="send-money-button"]');
    await page.click('[data-testid="confirm-button"]');

    // Should proceed with transaction
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Money sent successfully');
  });
});