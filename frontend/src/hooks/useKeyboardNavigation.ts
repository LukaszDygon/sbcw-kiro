/**
 * Keyboard navigation hook
 * Provides utilities for keyboard navigation and focus management
 */
import { useEffect, useRef, useCallback } from 'react'

interface UseKeyboardNavigationOptions {
  onEscape?: () => void
  onEnter?: () => void
  onArrowUp?: () => void
  onArrowDown?: () => void
  onArrowLeft?: () => void
  onArrowRight?: () => void
  onTab?: (event: KeyboardEvent) => void
  trapFocus?: boolean
  autoFocus?: boolean
}

export const useKeyboardNavigation = (options: UseKeyboardNavigationOptions = {}) => {
  const containerRef = useRef<HTMLElement>(null)
  const {
    onEscape,
    onEnter,
    onArrowUp,
    onArrowDown,
    onArrowLeft,
    onArrowRight,
    onTab,
    trapFocus = false,
    autoFocus = false,
  } = options

  // Get all focusable elements within the container
  const getFocusableElements = useCallback((): HTMLElement[] => {
    if (!containerRef.current) return []

    const focusableSelectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      'a[href]',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]',
    ].join(', ')

    return Array.from(containerRef.current.querySelectorAll(focusableSelectors))
  }, [])

  // Focus the first focusable element
  const focusFirst = useCallback(() => {
    const focusableElements = getFocusableElements()
    if (focusableElements.length > 0) {
      focusableElements[0].focus()
    }
  }, [getFocusableElements])

  // Focus the last focusable element
  const focusLast = useCallback(() => {
    const focusableElements = getFocusableElements()
    if (focusableElements.length > 0) {
      focusableElements[focusableElements.length - 1].focus()
    }
  }, [getFocusableElements])

  // Focus the next focusable element
  const focusNext = useCallback(() => {
    const focusableElements = getFocusableElements()
    const currentIndex = focusableElements.indexOf(document.activeElement as HTMLElement)
    
    if (currentIndex < focusableElements.length - 1) {
      focusableElements[currentIndex + 1].focus()
    } else if (trapFocus) {
      focusableElements[0].focus()
    }
  }, [getFocusableElements, trapFocus])

  // Focus the previous focusable element
  const focusPrevious = useCallback(() => {
    const focusableElements = getFocusableElements()
    const currentIndex = focusableElements.indexOf(document.activeElement as HTMLElement)
    
    if (currentIndex > 0) {
      focusableElements[currentIndex - 1].focus()
    } else if (trapFocus) {
      focusableElements[focusableElements.length - 1].focus()
    }
  }, [getFocusableElements, trapFocus])

  // Handle keyboard events
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    switch (event.key) {
      case 'Escape':
        if (onEscape) {
          event.preventDefault()
          onEscape()
        }
        break

      case 'Enter':
        if (onEnter) {
          event.preventDefault()
          onEnter()
        }
        break

      case 'ArrowUp':
        if (onArrowUp) {
          event.preventDefault()
          onArrowUp()
        }
        break

      case 'ArrowDown':
        if (onArrowDown) {
          event.preventDefault()
          onArrowDown()
        }
        break

      case 'ArrowLeft':
        if (onArrowLeft) {
          event.preventDefault()
          onArrowLeft()
        }
        break

      case 'ArrowRight':
        if (onArrowRight) {
          event.preventDefault()
          onArrowRight()
        }
        break

      case 'Tab':
        if (trapFocus) {
          event.preventDefault()
          if (event.shiftKey) {
            focusPrevious()
          } else {
            focusNext()
          }
        } else if (onTab) {
          onTab(event)
        }
        break

      default:
        break
    }
  }, [
    onEscape,
    onEnter,
    onArrowUp,
    onArrowDown,
    onArrowLeft,
    onArrowRight,
    onTab,
    trapFocus,
    focusNext,
    focusPrevious,
  ])

  // Set up event listeners
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.addEventListener('keydown', handleKeyDown)

    // Auto focus if requested
    if (autoFocus) {
      setTimeout(() => focusFirst(), 0)
    }

    return () => {
      container.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown, autoFocus, focusFirst])

  return {
    containerRef,
    focusFirst,
    focusLast,
    focusNext,
    focusPrevious,
    getFocusableElements,
  }
}

// Hook for managing focus trap in modals
export const useFocusTrap = (isActive: boolean = true) => {
  const { containerRef, focusFirst } = useKeyboardNavigation({
    trapFocus: isActive,
    autoFocus: isActive,
  })

  return { containerRef, focusFirst }
}

// Hook for arrow key navigation in lists
export const useArrowNavigation = (onSelect?: (index: number) => void) => {
  const currentIndex = useRef(0)
  const maxIndex = useRef(0)

  const setMaxIndex = useCallback((max: number) => {
    maxIndex.current = max
  }, [])

  const setCurrentIndex = useCallback((index: number) => {
    currentIndex.current = Math.max(0, Math.min(index, maxIndex.current))
  }, [])

  const { containerRef } = useKeyboardNavigation({
    onArrowUp: () => {
      currentIndex.current = Math.max(0, currentIndex.current - 1)
      if (onSelect) onSelect(currentIndex.current)
    },
    onArrowDown: () => {
      currentIndex.current = Math.min(maxIndex.current, currentIndex.current + 1)
      if (onSelect) onSelect(currentIndex.current)
    },
    onEnter: () => {
      if (onSelect) onSelect(currentIndex.current)
    },
  })

  return {
    containerRef,
    currentIndex: currentIndex.current,
    setMaxIndex,
    setCurrentIndex,
  }
}

export default useKeyboardNavigation