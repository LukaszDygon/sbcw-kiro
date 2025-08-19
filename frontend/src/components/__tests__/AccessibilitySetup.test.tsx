/**
 * Basic accessibility setup test
 * Verifies that accessibility testing infrastructure is working
 */
import React from 'react'
import { render } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { AccessibilityProvider } from '../../contexts/AccessibilityContext'

// Extend Jest matchers
expect.extend(toHaveNoViolations)

describe('Accessibility Setup', () => {
  it('should run axe tests without errors', async () => {
    const { container } = render(
      <AccessibilityProvider>
        <div>
          <h1>Test Heading</h1>
          <button>Test Button</button>
        </div>
      </AccessibilityProvider>
    )
    
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should provide accessibility context', () => {
    const TestComponent = () => {
      return <div data-testid="test">Accessibility context works</div>
    }

    const { getByTestId } = render(
      <AccessibilityProvider>
        <TestComponent />
      </AccessibilityProvider>
    )
    
    expect(getByTestId('test')).toBeInTheDocument()
  })
})