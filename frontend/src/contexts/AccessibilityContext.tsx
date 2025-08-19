/**
 * Accessibility Context for managing accessibility preferences
 * Provides theme, font size, and motion preferences
 */
import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'

export interface AccessibilityPreferences {
  theme: 'default' | 'high-contrast'
  fontSize: 'default' | 'large' | 'extra-large'
  reduceMotion: boolean
  screenReaderAnnouncements: boolean
}

interface AccessibilityContextType {
  preferences: AccessibilityPreferences
  updatePreferences: (updates: Partial<AccessibilityPreferences>) => void
  announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void
}

const defaultPreferences: AccessibilityPreferences = {
  theme: 'default',
  fontSize: 'default',
  reduceMotion: false,
  screenReaderAnnouncements: true,
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined)

interface AccessibilityProviderProps {
  children: ReactNode
}

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(defaultPreferences)

  // Load preferences from localStorage on mount
  useEffect(() => {
    const savedPreferences = localStorage.getItem('accessibility-preferences')
    if (savedPreferences) {
      try {
        const parsed = JSON.parse(savedPreferences)
        setPreferences({ ...defaultPreferences, ...parsed })
      } catch (error) {
        console.error('Failed to parse accessibility preferences:', error)
      }
    }

    // Check for system preferences
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches

    if (prefersReducedMotion || prefersHighContrast) {
      setPreferences(prev => ({
        ...prev,
        reduceMotion: prefersReducedMotion,
        theme: prefersHighContrast ? 'high-contrast' : prev.theme,
      }))
    }
  }, [])

  // Apply preferences to document
  useEffect(() => {
    const root = document.documentElement

    // Apply theme
    root.setAttribute('data-theme', preferences.theme)

    // Apply font size
    root.setAttribute('data-font-size', preferences.fontSize)

    // Apply motion preference
    if (preferences.reduceMotion) {
      root.style.setProperty('--animation-duration', '0.01ms')
    } else {
      root.style.removeProperty('--animation-duration')
    }

    // Save to localStorage
    localStorage.setItem('accessibility-preferences', JSON.stringify(preferences))
  }, [preferences])

  const updatePreferences = (updates: Partial<AccessibilityPreferences>) => {
    setPreferences(prev => ({ ...prev, ...updates }))
  }

  const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!preferences.screenReaderAnnouncements) return

    // Create or update the announcement element
    let announcer = document.getElementById('screen-reader-announcer')
    if (!announcer) {
      announcer = document.createElement('div')
      announcer.id = 'screen-reader-announcer'
      announcer.setAttribute('aria-live', priority)
      announcer.setAttribute('aria-atomic', 'true')
      announcer.className = 'sr-only'
      document.body.appendChild(announcer)
    }

    // Update the aria-live attribute if priority changed
    announcer.setAttribute('aria-live', priority)

    // Clear and set the message
    announcer.textContent = ''
    setTimeout(() => {
      announcer!.textContent = message
    }, 100)
  }

  const value: AccessibilityContextType = {
    preferences,
    updatePreferences,
    announceToScreenReader,
  }

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
    </AccessibilityContext.Provider>
  )
}

export const useAccessibility = (): AccessibilityContextType => {
  const context = useContext(AccessibilityContext)
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider')
  }
  return context
}

export default AccessibilityContext