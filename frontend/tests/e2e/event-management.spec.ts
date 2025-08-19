import { test, expect } from '@playwright/test';

test.describe('Event Management Flow', () => {
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

    // Mock balance
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

    // Mock active events
    await page.route('**/api/events', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          events: [
            {
              id: '1',
              name: 'Team Lunch',
              description: 'Monthly team lunch gathering',
              creator_name: 'John Doe',
              target_amount: '200.00',
              current_amount: '75.00',
              deadline: '2024-02-01T12:00:00Z',
              status: 'active',
              contributor_count: 3,
              created_at: '2024-01-15T10:00:00Z'
            },
            {
              id: '2',
              name: 'Office Party',
              description: 'End of year celebration',
              creator_name: 'Jane Smith',
              target_amount: '500.00',
              current_amount: '120.00',
              deadline: '2024-03-15T18:00:00Z',
              status: 'active',
              contributor_count: 5,
              created_at: '2024-01-10T14:30:00Z'
            }
          ]
        })
      });
    });
  });

  test('should create new event account', async ({ page }) => {
    // Mock event creation
    await page.route('**/api/events/create', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          event: {
            id: '3',
            name: 'Team Building',
            description: 'Quarterly team building activity',
            creator_name: 'Test User',
            target_amount: '300.00',
            current_amount: '0.00',
            deadline: '2024-04-01T12:00:00Z',
            status: 'active',
            contributor_count: 0,
            created_at: '2024-01-15T15:00:00Z'
          }
        })
      });
    });

    await page.goto('/events');

    // Click create event button
    await page.click('[data-testid="create-event-button"]');

    // Fill event form
    await page.fill('[data-testid="event-name-input"]', 'Team Building');
    await page.fill('[data-testid="event-description-input"]', 'Quarterly team building activity');
    await page.fill('[data-testid="target-amount-input"]', '300.00');
    
    // Set deadline (30 days from now)
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 30);
    const dateString = futureDate.toISOString().split('T')[0];
    await page.fill('[data-testid="deadline-input"]', dateString);

    // Submit form
    await page.click('[data-testid="create-event-submit"]');

    // Should show success message
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Event created successfully');
    
    // Should redirect to events list
    await expect(page).toHaveURL('/events');
    
    // New event should appear in list
    await expect(page.locator('[data-testid="event-card"]')).toContainText('Team Building');
  });

  test('should validate event creation form', async ({ page }) => {
    await page.goto('/events');
    await page.click('[data-testid="create-event-button"]');

    // Try to submit empty form
    await page.click('[data-testid="create-event-submit"]');

    // Should show validation errors
    await expect(page.locator('[data-testid="name-error"]')).toContainText('Event name is required');
    await expect(page.locator('[data-testid="description-error"]')).toContainText('Description is required');

    // Test invalid target amount
    await page.fill('[data-testid="target-amount-input"]', '-100');
    await page.blur('[data-testid="target-amount-input"]');
    await expect(page.locator('[data-testid="target-amount-error"]')).toContainText('Target amount must be positive');

    // Test past deadline
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 1);
    const pastDateString = pastDate.toISOString().split('T')[0];
    await page.fill('[data-testid="deadline-input"]', pastDateString);
    await page.blur('[data-testid="deadline-input"]');
    await expect(page.locator('[data-testid="deadline-error"]')).toContainText('Deadline must be in the future');
  });

  test('should contribute to existing event', async ({ page }) => {
    // Mock contribution
    await page.route('**/api/events/1/contribute', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          contribution: {
            id: 'contrib-123',
            amount: '25.00',
            contributor_name: 'Test User',
            note: 'Happy to contribute!',
            created_at: '2024-01-15T16:00:00Z'
          },
          contributor_balance: '125.00',
          event_total: '100.00'
        })
      });
    });

    await page.goto('/events');

    // Click on first event
    await page.click('[data-testid="event-card"]:first-child');

    // Should show event details
    await expect(page.locator('[data-testid="event-title"]')).toContainText('Team Lunch');
    await expect(page.locator('[data-testid="event-progress"]')).toContainText('£75.00 of £200.00');

    // Click contribute button
    await page.click('[data-testid="contribute-button"]');

    // Fill contribution form
    await page.fill('[data-testid="contribution-amount"]', '25.00');
    await page.fill('[data-testid="contribution-note"]', 'Happy to contribute!');

    // Submit contribution
    await page.click('[data-testid="submit-contribution"]');

    // Should show success message
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Contribution successful');
    
    // Should update event progress
    await expect(page.locator('[data-testid="event-progress"]')).toContainText('£100.00 of £200.00');
    
    // Should update user balance
    await expect(page.locator('[data-testid="user-balance"]')).toContainText('£125.00');
  });

  test('should display event progress and contributors', async ({ page }) => {
    // Mock event details with contributors
    await page.route('**/api/events/1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          event: {
            id: '1',
            name: 'Team Lunch',
            description: 'Monthly team lunch gathering',
            creator_name: 'John Doe',
            target_amount: '200.00',
            current_amount: '75.00',
            deadline: '2024-02-01T12:00:00Z',
            status: 'active',
            contributor_count: 3,
            created_at: '2024-01-15T10:00:00Z'
          },
          contributions: [
            {
              id: '1',
              contributor_name: 'Alice Johnson',
              amount: '30.00',
              note: 'Looking forward to it!',
              created_at: '2024-01-16T09:00:00Z'
            },
            {
              id: '2',
              contributor_name: 'Bob Wilson',
              amount: '25.00',
              note: 'Count me in',
              created_at: '2024-01-16T11:30:00Z'
            },
            {
              id: '3',
              contributor_name: 'Carol Davis',
              amount: '20.00',
              note: '',
              created_at: '2024-01-16T14:15:00Z'
            }
          ]
        })
      });
    });

    await page.goto('/events/1');

    // Should show event details
    await expect(page.locator('[data-testid="event-title"]')).toContainText('Team Lunch');
    await expect(page.locator('[data-testid="event-description"]')).toContainText('Monthly team lunch gathering');
    
    // Should show progress bar
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-percentage"]')).toContainText('37.5%'); // 75/200
    
    // Should show deadline
    await expect(page.locator('[data-testid="event-deadline"]')).toContainText('Feb 1, 2024');
    
    // Should show contributors list
    await expect(page.locator('[data-testid="contributor-list"]')).toContainText('Alice Johnson');
    await expect(page.locator('[data-testid="contributor-list"]')).toContainText('Bob Wilson');
    await expect(page.locator('[data-testid="contributor-list"]')).toContainText('Carol Davis');
    
    // Should show contribution amounts
    await expect(page.locator('[data-testid="contribution-amount"]')).toContainText('£30.00');
    await expect(page.locator('[data-testid="contribution-amount"]')).toContainText('£25.00');
    await expect(page.locator('[data-testid="contribution-amount"]')).toContainText('£20.00');
  });

  test('should handle contribution validation', async ({ page }) => {
    await page.goto('/events/1');
    await page.click('[data-testid="contribute-button"]');

    // Try to contribute negative amount
    await page.fill('[data-testid="contribution-amount"]', '-10');
    await page.blur('[data-testid="contribution-amount"]');
    await expect(page.locator('[data-testid="amount-error"]')).toContainText('Amount must be positive');

    // Try to contribute zero
    await page.fill('[data-testid="contribution-amount"]', '0');
    await page.blur('[data-testid="contribution-amount"]');
    await expect(page.locator('[data-testid="amount-error"]')).toContainText('Amount must be greater than zero');

    // Try to contribute more than available balance + overdraft
    await page.fill('[data-testid="contribution-amount"]', '500');
    await page.blur('[data-testid="contribution-amount"]');
    await expect(page.locator('[data-testid="amount-error"]')).toContainText('Amount exceeds available balance');
  });

  test('should close event (finance user)', async ({ page }) => {
    // Mock finance user
    await page.addInitScript(() => {
      localStorage.setItem('user', JSON.stringify({
        id: '1',
        name: 'Finance User',
        email: 'finance@company.com',
        role: 'finance'
      }));
    });

    // Mock event closure
    await page.route('**/api/events/1/close', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          event: {
            id: '1',
            name: 'Team Lunch',
            status: 'closed',
            closed_by: 'Finance User',
            closed_at: '2024-01-17T10:00:00Z',
            final_amount: '75.00'
          }
        })
      });
    });

    await page.goto('/events/1');

    // Finance user should see close button
    await expect(page.locator('[data-testid="close-event-button"]')).toBeVisible();

    // Click close event
    await page.click('[data-testid="close-event-button"]');

    // Should show confirmation dialog
    await expect(page.locator('[data-testid="close-confirmation"]')).toBeVisible();
    await expect(page.locator('[data-testid="close-confirmation"]')).toContainText('Are you sure you want to close this event?');

    // Fill closure reason
    await page.fill('[data-testid="closure-reason"]', 'Event completed successfully');

    // Confirm closure
    await page.click('[data-testid="confirm-close"]');

    // Should show success message
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Event closed successfully');
    
    // Should update event status
    await expect(page.locator('[data-testid="event-status"]')).toContainText('Closed');
    await expect(page.locator('[data-testid="closed-by"]')).toContainText('Closed by Finance User');
  });

  test('should filter and search events', async ({ page }) => {
    await page.goto('/events');

    // Should show all events initially
    await expect(page.locator('[data-testid="event-card"]')).toHaveLength(2);

    // Search by name
    await page.fill('[data-testid="search-input"]', 'lunch');
    await expect(page.locator('[data-testid="event-card"]')).toHaveLength(1);
    await expect(page.locator('[data-testid="event-card"]')).toContainText('Team Lunch');

    // Clear search
    await page.fill('[data-testid="search-input"]', '');
    await expect(page.locator('[data-testid="event-card"]')).toHaveLength(2);

    // Filter by status
    await page.selectOption('[data-testid="status-filter"]', 'active');
    await expect(page.locator('[data-testid="event-card"]')).toHaveLength(2);

    // Sort by deadline
    await page.selectOption('[data-testid="sort-select"]', 'deadline_asc');
    
    // First event should be Team Lunch (earlier deadline)
    const firstEvent = page.locator('[data-testid="event-card"]').first();
    await expect(firstEvent).toContainText('Team Lunch');
  });

  test('should show event deadline warnings', async ({ page }) => {
    // Mock event with approaching deadline
    await page.route('**/api/events', async route => {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          events: [
            {
              id: '1',
              name: 'Urgent Event',
              description: 'Event with approaching deadline',
              creator_name: 'John Doe',
              target_amount: '200.00',
              current_amount: '50.00',
              deadline: tomorrow.toISOString(),
              status: 'active',
              contributor_count: 2,
              created_at: '2024-01-15T10:00:00Z'
            }
          ]
        })
      });
    });

    await page.goto('/events');

    // Should show deadline warning
    await expect(page.locator('[data-testid="deadline-warning"]')).toBeVisible();
    await expect(page.locator('[data-testid="deadline-warning"]')).toContainText('Deadline approaching');
    
    // Event card should have warning styling
    await expect(page.locator('[data-testid="event-card"]')).toHaveClass(/deadline-warning/);
  });

  test('should handle event creation errors', async ({ page }) => {
    // Mock creation error
    await page.route('**/api/events/create', async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Event name already exists',
            details: {
              field: 'name',
              value: 'Team Lunch'
            }
          }
        })
      });
    });

    await page.goto('/events');
    await page.click('[data-testid="create-event-button"]');

    // Fill form with duplicate name
    await page.fill('[data-testid="event-name-input"]', 'Team Lunch');
    await page.fill('[data-testid="event-description-input"]', 'Another team lunch');
    await page.fill('[data-testid="target-amount-input"]', '150.00');

    await page.click('[data-testid="create-event-submit"]');

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Event name already exists');
    
    // Form should remain filled for correction
    await expect(page.locator('[data-testid="event-name-input"]')).toHaveValue('Team Lunch');
  });
});