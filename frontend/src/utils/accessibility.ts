/**
 * Accessibility utilities and testing helpers
 * Provides functions for accessibility testing and validation
 */

// Focus management utilities
export const focusManagement = {
  /**
   * Get all focusable elements within a container
   */
  getFocusableElements: (container: HTMLElement): HTMLElement[] => {
    const focusableSelectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      'a[href]',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]',
    ].join(', ')

    return Array.from(container.querySelectorAll(focusableSelectors))
  },

  /**
   * Trap focus within a container
   */
  trapFocus: (container: HTMLElement, event: KeyboardEvent) => {
    const focusableElements = focusManagement.getFocusableElements(container)
    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    if (event.key === 'Tab') {
      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault()
          lastElement.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault()
          firstElement.focus()
        }
      }
    }
  },

  /**
   * Restore focus to a previously focused element
   */
  restoreFocus: (element: HTMLElement | null) => {
    if (element && typeof element.focus === 'function') {
      element.focus()
    }
  },
}

// ARIA utilities
export const ariaUtils = {
  /**
   * Generate a unique ID for ARIA attributes
   */
  generateId: (prefix: string = 'aria'): string => {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`
  },

  /**
   * Set ARIA live region content
   */
  announce: (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    let announcer = document.getElementById('aria-live-announcer')
    
    if (!announcer) {
      announcer = document.createElement('div')
      announcer.id = 'aria-live-announcer'
      announcer.setAttribute('aria-live', priority)
      announcer.setAttribute('aria-atomic', 'true')
      announcer.className = 'sr-only'
      document.body.appendChild(announcer)
    }

    announcer.setAttribute('aria-live', priority)
    announcer.textContent = ''
    
    setTimeout(() => {
      announcer!.textContent = message
    }, 100)
  },

  /**
   * Check if an element has proper ARIA labeling
   */
  hasAccessibleName: (element: HTMLElement): boolean => {
    return !!(
      element.getAttribute('aria-label') ||
      element.getAttribute('aria-labelledby') ||
      element.textContent?.trim() ||
      (element as HTMLInputElement).labels?.length
    )
  },
}

// Color contrast utilities
export const colorContrast = {
  /**
   * Calculate relative luminance of a color
   */
  getLuminance: (r: number, g: number, b: number): number => {
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
    })
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
  },

  /**
   * Calculate contrast ratio between two colors
   */
  getContrastRatio: (color1: [number, number, number], color2: [number, number, number]): number => {
    const lum1 = colorContrast.getLuminance(...color1)
    const lum2 = colorContrast.getLuminance(...color2)
    const brightest = Math.max(lum1, lum2)
    const darkest = Math.min(lum1, lum2)
    return (brightest + 0.05) / (darkest + 0.05)
  },

  /**
   * Check if contrast ratio meets WCAG AA standards
   */
  meetsWCAGAA: (contrastRatio: number, isLargeText: boolean = false): boolean => {
    return contrastRatio >= (isLargeText ? 3 : 4.5)
  },

  /**
   * Check if contrast ratio meets WCAG AAA standards
   */
  meetsWCAGAAA: (contrastRatio: number, isLargeText: boolean = false): boolean => {
    return contrastRatio >= (isLargeText ? 4.5 : 7)
  },
}

// Keyboard navigation utilities
export const keyboardUtils = {
  /**
   * Check if an element is keyboard accessible
   */
  isKeyboardAccessible: (element: HTMLElement): boolean => {
    const tabIndex = element.getAttribute('tabindex')
    return (
      element.tagName === 'BUTTON' ||
      element.tagName === 'INPUT' ||
      element.tagName === 'SELECT' ||
      element.tagName === 'TEXTAREA' ||
      element.tagName === 'A' ||
      (tabIndex !== null && tabIndex !== '-1')
    )
  },

  /**
   * Get the next focusable element in tab order
   */
  getNextFocusableElement: (currentElement: HTMLElement): HTMLElement | null => {
    const focusableElements = focusManagement.getFocusableElements(document.body)
    const currentIndex = focusableElements.indexOf(currentElement)
    return focusableElements[currentIndex + 1] || null
  },

  /**
   * Get the previous focusable element in tab order
   */
  getPreviousFocusableElement: (currentElement: HTMLElement): HTMLElement | null => {
    const focusableElements = focusManagement.getFocusableElements(document.body)
    const currentIndex = focusableElements.indexOf(currentElement)
    return focusableElements[currentIndex - 1] || null
  },
}

// Screen reader utilities
export const screenReaderUtils = {
  /**
   * Check if screen reader is likely being used
   */
  isScreenReaderActive: (): boolean => {
    // This is a heuristic and not 100% reliable
    return (
      window.navigator.userAgent.includes('NVDA') ||
      window.navigator.userAgent.includes('JAWS') ||
      window.speechSynthesis?.speaking ||
      false
    )
  },

  /**
   * Create screen reader friendly text for complex UI elements
   */
  createAccessibleDescription: (element: HTMLElement): string => {
    const role = element.getAttribute('role') || element.tagName.toLowerCase()
    const label = element.getAttribute('aria-label') || element.textContent?.trim() || ''
    const expanded = element.getAttribute('aria-expanded')
    const selected = element.getAttribute('aria-selected')
    const checked = element.getAttribute('aria-checked') || (element as HTMLInputElement).checked

    let description = `${role} ${label}`

    if (expanded !== null) {
      description += expanded === 'true' ? ' expanded' : ' collapsed'
    }

    if (selected !== null) {
      description += selected === 'true' ? ' selected' : ' not selected'
    }

    if (checked !== null) {
      description += checked ? ' checked' : ' not checked'
    }

    return description.trim()
  },
}

// Accessibility testing utilities
export const a11yTesting = {
  /**
   * Run basic accessibility checks on an element
   */
  runBasicChecks: (element: HTMLElement): string[] => {
    const issues: string[] = []

    // Check for missing alt text on images
    if (element.tagName === 'IMG' && !element.getAttribute('alt')) {
      issues.push('Image missing alt text')
    }

    // Check for missing labels on form inputs
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName)) {
      const input = element as HTMLInputElement
      if (!input.labels?.length && !element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
        issues.push('Form input missing accessible label')
      }
    }

    // Check for missing accessible names on interactive elements
    if (['BUTTON', 'A'].includes(element.tagName)) {
      if (!ariaUtils.hasAccessibleName(element)) {
        issues.push('Interactive element missing accessible name')
      }
    }

    // Check for keyboard accessibility
    if (element.onclick && !keyboardUtils.isKeyboardAccessible(element)) {
      issues.push('Clickable element not keyboard accessible')
    }

    return issues
  },

  /**
   * Check if element meets minimum touch target size (44x44px)
   */
  meetsTouchTargetSize: (element: HTMLElement): boolean => {
    const rect = element.getBoundingClientRect()
    return rect.width >= 44 && rect.height >= 44
  },

  /**
   * Generate accessibility report for an element and its children
   */
  generateReport: (container: HTMLElement): {
    totalElements: number
    issues: Array<{ element: HTMLElement; issues: string[] }>
    summary: { [key: string]: number }
  } => {
    const allElements = container.querySelectorAll('*')
    const issues: Array<{ element: HTMLElement; issues: string[] }> = []
    const summary: { [key: string]: number } = {}

    allElements.forEach(el => {
      const elementIssues = a11yTesting.runBasicChecks(el as HTMLElement)
      if (elementIssues.length > 0) {
        issues.push({ element: el as HTMLElement, issues: elementIssues })
        elementIssues.forEach(issue => {
          summary[issue] = (summary[issue] || 0) + 1
        })
      }
    })

    return {
      totalElements: allElements.length,
      issues,
      summary,
    }
  },
}

export default {
  focusManagement,
  ariaUtils,
  colorContrast,
  keyboardUtils,
  screenReaderUtils,
  a11yTesting,
}