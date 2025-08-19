/**
 * Responsive Navigation component
 * Mobile-first navigation with accessibility features
 */
import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useKeyboardNavigation } from '../../hooks/useKeyboardNavigation'
import { useAccessibility } from '../../contexts/AccessibilityContext'

interface NavigationItem {
  label: string
  href: string
  icon?: React.ReactNode
  badge?: string | number
  description?: string
}

interface ResponsiveNavigationProps {
  items: NavigationItem[]
  logo?: React.ReactNode
  userMenu?: React.ReactNode
  className?: string
}

const ResponsiveNavigation: React.FC<ResponsiveNavigationProps> = ({
  items,
  logo,
  userMenu,
  className = '',
}) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()
  const { announceToScreenReader } = useAccessibility()
  const { containerRef } = useKeyboardNavigation({
    onEscape: () => {
      if (isMobileMenuOpen) {
        setIsMobileMenuOpen(false)
        announceToScreenReader('Mobile menu closed')
      }
    },
  })

  const toggleMobileMenu = () => {
    const newState = !isMobileMenuOpen
    setIsMobileMenuOpen(newState)
    announceToScreenReader(newState ? 'Mobile menu opened' : 'Mobile menu closed')
  }

  const isCurrentPage = (href: string) => {
    return location.pathname === href
  }

  return (
    <nav 
      className={`bg-white shadow-sm border-b border-gray-200 ${className}`}
      role="navigation"
      aria-label="Main navigation"
      ref={containerRef}
    >
      <div className="container-responsive">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            {logo}
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex md:items-center md:space-x-8">
            {items.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  isCurrentPage(item.href)
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                }`}
                aria-current={isCurrentPage(item.href) ? 'page' : undefined}
                aria-describedby={item.description ? `nav-desc-${item.href}` : undefined}
              >
                <div className="flex items-center space-x-2">
                  {item.icon && (
                    <span className="flex-shrink-0" aria-hidden="true">
                      {item.icon}
                    </span>
                  )}
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </div>
                {item.description && (
                  <span id={`nav-desc-${item.href}`} className="sr-only">
                    {item.description}
                  </span>
                )}
              </Link>
            ))}
          </div>

          {/* User Menu and Mobile Menu Button */}
          <div className="flex items-center space-x-4">
            {userMenu}
            
            {/* Mobile menu button */}
            <button
              type="button"
              className="md:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              aria-controls="mobile-menu"
              aria-expanded={isMobileMenuOpen}
              onClick={toggleMobileMenu}
            >
              <span className="sr-only">
                {isMobileMenuOpen ? 'Close main menu' : 'Open main menu'}
              </span>
              {isMobileMenuOpen ? (
                <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="block h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        <div 
          className={`md:hidden ${isMobileMenuOpen ? 'block' : 'hidden'}`}
          id="mobile-menu"
        >
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 border-t border-gray-200">
            {items.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className={`block px-3 py-2 rounded-md text-base font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 touch-target ${
                  isCurrentPage(item.href)
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                }`}
                aria-current={isCurrentPage(item.href) ? 'page' : undefined}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {item.icon && (
                      <span className="flex-shrink-0" aria-hidden="true">
                        {item.icon}
                      </span>
                    )}
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="bg-red-100 text-red-800 text-xs font-medium px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </div>
                {item.description && (
                  <div className="mt-1 text-sm text-gray-500">
                    {item.description}
                  </div>
                )}
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Mobile menu overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black bg-opacity-25 md:hidden"
          aria-hidden="true"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </nav>
  )
}

export default ResponsiveNavigation