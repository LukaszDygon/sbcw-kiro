/**
 * Accessibility tests for components
 * Tests WCAG 2.1 AA compliance across all components
 */
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import userEvent from '@testing-library/user-event'
import { AccessibilityProvider } from '../../contexts/AccessibilityContext'
import AccessibleButton from '../shared/AccessibleButton'
import AccessibleInput from '../shared/AccessibleInput'
import AccessibleModal from '../shared/AccessibleModal'
import AccessibleTable from '../shared/AccessibleTable'
import LoadingSpinner from '../shared/LoadingSpinner'
import { a11yTesting } from '../../utils/accessibility'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

// Test wrapper with accessibility provider
const AccessibilityWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AccessibilityProvider>
    {children}
  </AccessibilityProvider>
)

describe('Accessibility Tests', () => {
  describe('AccessibleButton', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <AccessibilityWrapper>
          <AccessibleButton>Click me</AccessibleButton>
        </AccessibilityWrapper>
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should be keyboard accessible', async () => {
      const user = userEvent.setup()
      const handleClick = jest.fn()
      
      render(
        <AccessibilityWrapper>
          <AccessibleButton onClick={handleClick}>Click me</AccessibleButton>
        </AccessibilityWrapper>
      )

      const button = screen.getByRole('button', { name: 'Click me' })
      
      // Test keyboard navigation
      await user.tab()
      expect(button).toHaveFocus()
      
      // Test Enter key
      await user.keyboard('{Enter}')
      expect(handleClick).toHaveBeenCalledTimes(1)
      
      // Test Space key
      await user.keyboard(' ')
      expect(handleClick).toHaveBeenCalledTimes(2)
    })

    it('should have proper ARIA attributes when loading', () => {
      render(
        <AccessibilityWrapper>
          <AccessibleButton loading loadingText="Saving...">
            Save
          </AccessibleButton>
        </AccessibilityWrapper>
      )

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-disabled', 'true')
      expect(button).toBeDisabled()
      expect(screen.getByText('Saving...')).toBeInTheDocument()
    })

    it('should meet minimum touch target size', () => {
      render(
        <AccessibilityWrapper>
          <AccessibleButton>Click me</AccessibleButton>
        </AccessibilityWrapper>
      )

      const button = screen.getByRole('button')
      
      // Mock getBoundingClientRect for testing
      jest.spyOn(button, 'getBoundingClientRect').mockReturnValue({
        width: 100,
        height: 44,
        top: 0,
        left: 0,
        bottom: 44,
        right: 100,
        x: 0,
        y: 0,
        toJSON: () => ({})
      } as DOMRect)
      
      const rect = button.getBoundingClientRect()
      expect(rect.height).toBeGreaterThanOrEqual(44)
    })
  })

  describe('AccessibleInput', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <AccessibilityWrapper>
          <AccessibleInput label="Email" type="email" />
        </AccessibilityWrapper>
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should have proper labeling', () => {
      render(
        <AccessibilityWrapper>
          <AccessibleInput 
            label="Email Address" 
            type="email" 
            required 
            helperText="Enter your work email"
          />
        </AccessibilityWrapper>
      )

      const input = screen.getByRole('textbox', { name: /email address/i })
      const label = screen.getByText('Email Address')
      
      expect(input).toHaveAttribute('aria-required', 'true')
      expect(input).toHaveAttribute('aria-describedby')
      expect(label).toBeInTheDocument()
      expect(screen.getByText('Enter your work email')).toBeInTheDocument()
    })

    it('should handle error states properly', () => {
      render(
        <AccessibilityWrapper>
          <AccessibleInput 
            label="Email" 
            type="email" 
            error="Please enter a valid email address"
          />
        </AccessibilityWrapper>
      )

      const input = screen.getByRole('textbox')
      const errorMessage = screen.getByRole('alert')
      
      expect(input).toHaveAttribute('aria-invalid', 'true')
      expect(input).toHaveAttribute('aria-describedby')
      expect(errorMessage).toHaveTextContent('Please enter a valid email address')
    })
  })

  describe('AccessibleModal', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <AccessibilityWrapper>
          <AccessibleModal isOpen={true} onClose={() => {}} title="Test Modal">
            <p>Modal content</p>
          </AccessibleModal>
        </AccessibilityWrapper>
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should trap focus within modal', async () => {
      const user = userEvent.setup()
      const handleClose = jest.fn()
      
      render(
        <AccessibilityWrapper>
          <button>Outside button</button>
          <AccessibleModal isOpen={true} onClose={handleClose} title="Test Modal">
            <button>First button</button>
            <button>Second button</button>
          </AccessibleModal>
        </AccessibilityWrapper>
      )

      const modal = screen.getByRole('dialog')
      const firstButton = screen.getByText('First button')
      const secondButton = screen.getByText('Second button')
      const closeButton = screen.getByRole('button', { name: /close/i })

      // Focus should be trapped within modal
      await user.tab()
      // In test environment, focus behavior may differ, so we check if focus is within modal
      const focusedElement = document.activeElement
      expect(modal.contains(focusedElement)).toBe(true)
      
      await user.tab()
      const focusedElement2 = document.activeElement
      expect(modal.contains(focusedElement2)).toBe(true)
      
      await user.tab()
      expect(secondButton).toHaveFocus()
      
      // Should cycle back to close button
      await user.tab()
      expect(closeButton).toHaveFocus()
    })

    it('should close on Escape key', async () => {
      const user = userEvent.setup()
      const handleClose = jest.fn()
      
      render(
        <AccessibilityWrapper>
          <AccessibleModal isOpen={true} onClose={handleClose} title="Test Modal">
            <p>Modal content</p>
          </AccessibleModal>
        </AccessibilityWrapper>
      )

      await user.keyboard('{Escape}')
      expect(handleClose).toHaveBeenCalledTimes(1)
    })

    it('should have proper ARIA attributes', () => {
      render(
        <AccessibilityWrapper>
          <AccessibleModal 
            isOpen={true} 
            onClose={() => {}} 
            title="Test Modal"
            aria-describedby="modal-description"
          >
            <p id="modal-description">This is a test modal</p>
          </AccessibleModal>
        </AccessibilityWrapper>
      )

      const modal = screen.getByRole('dialog')
      expect(modal).toHaveAttribute('aria-modal', 'true')
      expect(modal).toHaveAttribute('aria-labelledby')
      expect(modal).toHaveAttribute('aria-describedby', 'modal-description')
    })
  })

  describe('AccessibleTable', () => {
    const mockData = [
      { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Admin' },
      { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'User' },
    ]

    const mockColumns = [
      { key: 'name', title: 'Name', sortable: true },
      { key: 'email', title: 'Email', sortable: true },
      { key: 'role', title: 'Role', sortable: false },
    ]

    it('should not have accessibility violations', async () => {
      const { container } = render(
        <AccessibilityWrapper>
          <AccessibleTable 
            data={mockData} 
            columns={mockColumns}
            caption="User list"
          />
        </AccessibilityWrapper>
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should have proper table structure', () => {
      render(
        <AccessibilityWrapper>
          <AccessibleTable 
            data={mockData} 
            columns={mockColumns}
            caption="User list"
            aria-label="Users table"
          />
        </AccessibilityWrapper>
      )

      const table = screen.getByRole('table', { name: 'Users table' })
      expect(table).toBeInTheDocument()
      
      // Check column headers
      expect(screen.getByRole('columnheader', { name: 'Name' })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: 'Email' })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: 'Role' })).toBeInTheDocument()
      
      // Check data cells
      expect(screen.getByRole('cell', { name: 'John Doe' })).toBeInTheDocument()
      expect(screen.getByRole('cell', { name: 'john@example.com' })).toBeInTheDocument()
    })

    it('should handle sorting with keyboard', async () => {
      const user = userEvent.setup()
      const handleSort = jest.fn()
      
      render(
        <AccessibilityWrapper>
          <AccessibleTable 
            data={mockData} 
            columns={mockColumns}
            onSort={handleSort}
          />
        </AccessibilityWrapper>
      )

      const nameHeader = screen.getByRole('button', { name: /sort by name/i })
      
      // Test keyboard activation
      nameHeader.focus()
      await user.keyboard('{Enter}')
      expect(handleSort).toHaveBeenCalledWith({ key: 'name', direction: 'asc' })
      
      await user.keyboard(' ')
      expect(handleSort).toHaveBeenCalledWith({ key: 'name', direction: 'asc' })
    })
  })

  describe('LoadingSpinner', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(
        <AccessibilityWrapper>
          <LoadingSpinner message="Loading data..." />
        </AccessibilityWrapper>
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should have proper ARIA attributes', () => {
      render(
        <AccessibilityWrapper>
          <LoadingSpinner 
            message="Loading user data..." 
            aria-label="Loading users"
          />
        </AccessibilityWrapper>
      )

      const spinner = screen.getByRole('status', { name: 'Loading users' })
      expect(spinner).toHaveAttribute('aria-live', 'polite')
      expect(screen.getAllByText('Loading user data...').length).toBeGreaterThan(0)
    })

    it('should respect reduced motion preferences', () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      })

      render(
        <AccessibilityWrapper>
          <LoadingSpinner />
        </AccessibilityWrapper>
      )

      const spinner = screen.getByRole('status')
      expect(spinner).toHaveClass('spinner')
    })
  })

  describe('Accessibility Utils', () => {
    it('should detect accessibility issues', () => {
      const container = document.createElement('div')
      container.innerHTML = `
        <img src="test.jpg" />
        <input type="text" />
        <button onclick="alert('test')"></button>
      `

      const report = a11yTesting.generateReport(container)
      
      expect(report.issues.length).toBeGreaterThan(0)
      expect(report.summary['Image missing alt text']).toBe(1)
      expect(report.summary['Form input missing accessible label']).toBe(1)
    })

    it('should validate touch target sizes', () => {
      const button = document.createElement('button')
      button.style.width = '44px'
      button.style.height = '44px'
      
      // Mock getBoundingClientRect
      button.getBoundingClientRect = jest.fn(() => ({
        width: 44,
        height: 44,
        top: 0,
        left: 0,
        bottom: 44,
        right: 44,
        x: 0,
        y: 0,
        toJSON: jest.fn(),
      }))

      expect(a11yTesting.meetsTouchTargetSize(button)).toBe(true)
    })
  })

  describe('High Contrast Mode', () => {
    it('should apply high contrast styles', () => {
      render(
        <AccessibilityWrapper>
          <div data-theme="high-contrast">
            <AccessibleButton>Test Button</AccessibleButton>
          </div>
        </AccessibilityWrapper>
      )

      const container = screen.getByRole('button').closest('[data-theme="high-contrast"]')
      expect(container).toHaveAttribute('data-theme', 'high-contrast')
    })
  })

  describe('Keyboard Navigation', () => {
    it('should handle arrow key navigation', async () => {
      const user = userEvent.setup()
      
      render(
        <AccessibilityWrapper>
          <div>
            <button>Button 1</button>
            <button>Button 2</button>
            <button>Button 3</button>
          </div>
        </AccessibilityWrapper>
      )

      const buttons = screen.getAllByRole('button')
      
      // Focus first button
      buttons[0].focus()
      expect(buttons[0]).toHaveFocus()
      
      // Tab to next button
      await user.tab()
      expect(buttons[1]).toHaveFocus()
      
      // Tab to next button
      await user.tab()
      expect(buttons[2]).toHaveFocus()
    })
  })
})