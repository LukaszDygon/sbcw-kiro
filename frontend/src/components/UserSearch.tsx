/**
 * UserSearch component for finding users for transactions
 * Provides autocomplete search functionality
 */
import React, { useState, useEffect, useRef } from 'react'
import { authService } from '../services/auth'

export interface User {
  id: string
  name: string
  email: string
  role: string
}

interface UserSearchProps {
  onUserSelect: (user: User) => void
  selectedUser?: User | null
  placeholder?: string
  excludeSelf?: boolean
  className?: string
  disabled?: boolean
}

const UserSearch: React.FC<UserSearchProps> = ({
  onUserSelect,
  selectedUser,
  placeholder = "Search for users...",
  excludeSelf = true,
  className = '',
  disabled = false
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [highlightedIndex, setHighlightedIndex] = useState(-1)
  
  const searchRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchTimeoutRef = useRef<NodeJS.Timeout>()

  // Handle search with debouncing
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    if (searchTerm.length >= 2) {
      searchTimeoutRef.current = setTimeout(() => {
        performSearch(searchTerm)
      }, 300)
    } else {
      setUsers([])
      setShowDropdown(false)
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [searchTerm])

  // Handle clicks outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !searchRef.current?.contains(event.target as Node)
      ) {
        setShowDropdown(false)
        setHighlightedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const performSearch = async (term: string) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await authService.searchUsers(term, {
        limit: 10,
        exclude_self: excludeSelf
      })
      
      setUsers(response.users)
      setShowDropdown(true)
      setHighlightedIndex(-1)
    } catch (error: any) {
      console.error('User search failed:', error)
      setError(error.message || 'Failed to search users')
      setUsers([])
      setShowDropdown(false)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setSearchTerm(value)
    
    // Clear selection if user is typing
    if (selectedUser && value !== selectedUser.name) {
      onUserSelect(null as any)
    }
  }

  const handleUserSelect = (user: User) => {
    setSearchTerm(user.name)
    setShowDropdown(false)
    setHighlightedIndex(-1)
    onUserSelect(user)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || users.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev => 
          prev < users.length - 1 ? prev + 1 : 0
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : users.length - 1
        )
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex >= 0 && highlightedIndex < users.length) {
          handleUserSelect(users[highlightedIndex])
        }
        break
      case 'Escape':
        setShowDropdown(false)
        setHighlightedIndex(-1)
        searchRef.current?.blur()
        break
    }
  }

  const handleFocus = () => {
    if (searchTerm.length >= 2 && users.length > 0) {
      setShowDropdown(true)
    }
  }

  const clearSelection = () => {
    setSearchTerm('')
    setShowDropdown(false)
    setHighlightedIndex(-1)
    onUserSelect(null as any)
    searchRef.current?.focus()
  }

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        
        <input
          ref={searchRef}
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder={placeholder}
          disabled={disabled}
          className={`block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 ${
            disabled ? 'bg-gray-100 cursor-not-allowed' : ''
          } ${
            selectedUser ? 'border-green-500 bg-green-50' : ''
          }`}
        />
        
        {/* Loading spinner */}
        {loading && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <svg className="animate-spin h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        )}
        
        {/* Clear button */}
        {searchTerm && !loading && (
          <button
            onClick={clearSelection}
            className="absolute inset-y-0 right-0 pr-3 flex items-center hover:text-gray-600"
          >
            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Dropdown */}
      {showDropdown && (
        <div
          ref={dropdownRef}
          className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none"
        >
          {users.length > 0 ? (
            users.map((user, index) => (
              <button
                key={user.id}
                onClick={() => handleUserSelect(user)}
                className={`w-full text-left px-4 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none ${
                  index === highlightedIndex ? 'bg-blue-100' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-gray-900">{user.name}</div>
                    <div className="text-sm text-gray-500">{user.email}</div>
                  </div>
                  <div className="text-xs text-gray-400 uppercase">
                    {user.role}
                  </div>
                </div>
              </button>
            ))
          ) : (
            <div className="px-4 py-2 text-sm text-gray-500">
              {searchTerm.length < 2 
                ? 'Type at least 2 characters to search'
                : 'No users found'
              }
            </div>
          )}
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mt-1 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Selected user indicator */}
      {selectedUser && (
        <div className="mt-2 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
          <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Selected: {selectedUser.name}
        </div>
      )}
    </div>
  )
}

export default UserSearch