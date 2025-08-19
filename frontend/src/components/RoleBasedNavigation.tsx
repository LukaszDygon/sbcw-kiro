/**
 * Role-based navigation component
 * Renders navigation items based on user roles and permissions
 */
import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from './AuthGuard'

interface NavigationItem {
  name: string
  href: string
  icon?: React.ComponentType<{ className?: string }>
  requiredRoles?: string[]
  requiredPermissions?: string[]
  requireAll?: boolean
  badge?: string | number
  children?: NavigationItem[]
}

interface RoleBasedNavigationProps {
  items: NavigationItem[]
  className?: string
  orientation?: 'horizontal' | 'vertical'
  showIcons?: boolean
  showBadges?: boolean
}

const RoleBasedNavigation: React.FC<RoleBasedNavigationProps> = ({
  items,
  className = '',
  orientation = 'horizontal',
  showIcons = true,
  showBadges = true
}) => {
  const { user, hasAnyRole, hasAnyPermission, hasAllPermissions } = useAuth()

  const hasAccess = (item: NavigationItem): boolean => {
    // Check role requirements
    if (item.requiredRoles && item.requiredRoles.length > 0) {
      if (!hasAnyRole(item.requiredRoles)) {
        return false
      }
    }

    // Check permission requirements
    if (item.requiredPermissions && item.requiredPermissions.length > 0) {
      const hasPermissions = item.requireAll
        ? hasAllPermissions(item.requiredPermissions)
        : hasAnyPermission(item.requiredPermissions)
      
      if (!hasPermissions) {
        return false
      }
    }

    return true
  }

  const renderNavigationItem = (item: NavigationItem, isChild = false) => {
    if (!hasAccess(item)) {
      return null
    }

    const baseClasses = isChild
      ? 'block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900'
      : orientation === 'horizontal'
      ? 'inline-flex items-center px-3 py-2 text-sm font-medium rounded-md'
      : 'flex items-center px-3 py-2 text-sm font-medium rounded-md'

    const activeClasses = isChild
      ? 'bg-gray-100 text-gray-900'
      : 'bg-blue-100 text-blue-700'

    const inactiveClasses = isChild
      ? 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'

    return (
      <div key={item.name} className="relative">
        <NavLink
          to={item.href}
          className={({ isActive }) =>
            `${baseClasses} ${isActive ? activeClasses : inactiveClasses}`
          }
        >
          {showIcons && item.icon && (
            <item.icon className={`${isChild ? 'mr-2 h-4 w-4' : 'mr-2 h-5 w-5'}`} />
          )}
          <span>{item.name}</span>
          {showBadges && item.badge && (
            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
              {item.badge}
            </span>
          )}
        </NavLink>

        {/* Render children as dropdown or submenu */}
        {item.children && item.children.length > 0 && (
          <div className="ml-4 mt-1 space-y-1">
            {item.children.map(child => renderNavigationItem(child, true))}
          </div>
        )}
      </div>
    )
  }

  if (!user) {
    return null
  }

  const containerClasses = orientation === 'horizontal'
    ? `flex space-x-4 ${className}`
    : `space-y-1 ${className}`

  return (
    <nav className={containerClasses}>
      {items.map(item => renderNavigationItem(item))}
    </nav>
  )
}

export default RoleBasedNavigation

// Default navigation items for SoftBankCashWire
export const defaultNavigationItems: NavigationItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2z" />
      </svg>
    )
  },
  {
    name: 'Transactions',
    href: '/transactions',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
      </svg>
    ),
    children: [
      {
        name: 'Send Money',
        href: '/transactions/send'
      },
      {
        name: 'Transaction History',
        href: '/transactions/history'
      },
      {
        name: 'Bulk Transfer',
        href: '/transactions/bulk',
        requiredRoles: ['ADMIN', 'FINANCE']
      }
    ]
  },
  {
    name: 'Money Requests',
    href: '/money-requests',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0h6a2 2 0 012 2v10a2 2 0 01-2 2H8a2 2 0 01-2-2V9a2 2 0 012-2z" />
      </svg>
    ),
    children: [
      {
        name: 'Create Request',
        href: '/money-requests/create'
      },
      {
        name: 'Pending Requests',
        href: '/money-requests/pending'
      },
      {
        name: 'Request History',
        href: '/money-requests/history'
      }
    ]
  },
  {
    name: 'Events',
    href: '/events',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0h6a2 2 0 012 2v10a2 2 0 01-2 2H8a2 2 0 01-2-2V9a2 2 0 012-2z" />
      </svg>
    ),
    children: [
      {
        name: 'Active Events',
        href: '/events/active'
      },
      {
        name: 'Create Event',
        href: '/events/create'
      },
      {
        name: 'My Events',
        href: '/events/my-events'
      },
      {
        name: 'My Contributions',
        href: '/events/contributions'
      }
    ]
  },
  {
    name: 'Reports',
    href: '/reports',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    children: [
      {
        name: 'Personal Analytics',
        href: '/reports/personal'
      },
      {
        name: 'Transaction Summary',
        href: '/reports/transactions'
      },
      {
        name: 'User Activity',
        href: '/reports/user-activity',
        requiredRoles: ['ADMIN', 'FINANCE']
      },
      {
        name: 'Event Reports',
        href: '/reports/events',
        requiredRoles: ['ADMIN', 'FINANCE']
      }
    ]
  },
  {
    name: 'Admin',
    href: '/admin',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    requiredRoles: ['ADMIN'],
    children: [
      {
        name: 'User Management',
        href: '/admin/users'
      },
      {
        name: 'System Settings',
        href: '/admin/settings'
      },
      {
        name: 'Security Monitor',
        href: '/admin/security'
      },
      {
        name: 'System Statistics',
        href: '/admin/statistics'
      }
    ]
  },
  {
    name: 'Audit',
    href: '/audit',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    requiredRoles: ['FINANCE', 'ADMIN'],
    children: [
      {
        name: 'Audit Logs',
        href: '/audit/logs'
      },
      {
        name: 'Compliance Reports',
        href: '/audit/compliance'
      },
      {
        name: 'Data Integrity',
        href: '/audit/integrity',
        requiredRoles: ['ADMIN']
      }
    ]
  }
]

// User menu items
export const userMenuItems: NavigationItem[] = [
  {
    name: 'Profile',
    href: '/profile',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    )
  },
  {
    name: 'Account Settings',
    href: '/settings',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    )
  },
  {
    name: 'Help & Support',
    href: '/help',
    icon: ({ className }) => (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    )
  }
]