/**
 * Accessible Table component
 * WCAG 2.1 AA compliant table with keyboard navigation and screen reader support
 */
import React from 'react'
import { useKeyboardNavigation } from '../../hooks/useKeyboardNavigation'
import LoadingSpinner from './LoadingSpinner'

export interface Column<T> {
  key: string
  title: string
  sortable?: boolean
  className?: string
  render?: (value: any, item: T, index: number) => React.ReactNode
}

export interface SortConfig {
  key: string
  direction: 'asc' | 'desc'
}

interface AccessibleTableProps<T> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  error?: string | null
  emptyMessage?: string
  caption?: string
  sortConfig?: SortConfig
  onSort?: (sortConfig: SortConfig) => void
  className?: string
  'aria-label'?: string
}

function AccessibleTable<T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  error = null,
  emptyMessage = 'No data available',
  caption,
  sortConfig,
  onSort,
  className = '',
  'aria-label': ariaLabel,
}: AccessibleTableProps<T>) {
  const { containerRef } = useKeyboardNavigation()

  const handleSort = (columnKey: string) => {
    if (!onSort) return

    const newDirection = 
      sortConfig?.key === columnKey && sortConfig.direction === 'asc' 
        ? 'desc' 
        : 'asc'

    onSort({ key: columnKey, direction: newDirection })
  }

  const getSortIcon = (columnKey: string) => {
    if (!sortConfig || sortConfig.key !== columnKey) {
      return (
        <svg className="w-4 h-4 ml-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      )
    }

    return sortConfig.direction === 'asc' ? (
      <svg className="w-4 h-4 ml-1 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg className="w-4 h-4 ml-1 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    )
  }

  const getSortAriaLabel = (column: Column<T>) => {
    if (!column.sortable) return undefined

    const currentSort = sortConfig?.key === column.key ? sortConfig.direction : null
    if (currentSort === 'asc') {
      return `Sort ${column.title} descending`
    } else if (currentSort === 'desc') {
      return `Sort ${column.title} ascending`
    } else {
      return `Sort by ${column.title}`
    }
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center">
          <div className="text-red-600 mb-2">
            <svg className="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Data</h3>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white shadow rounded-lg overflow-hidden ${className}`} ref={containerRef}>
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
          <LoadingSpinner size="medium" message="Loading data..." />
        </div>
      )}

      <div className="overflow-x-auto">
        <table 
          className="table min-w-full divide-y divide-gray-200"
          aria-label={ariaLabel}
        >
          {caption && (
            <caption className="sr-only">
              {caption}
            </caption>
          )}
          
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${column.className || ''}`}
                >
                  {column.sortable ? (
                    <button
                      type="button"
                      className="group inline-flex items-center space-x-1 text-left font-medium text-gray-500 uppercase tracking-wider hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                      onClick={() => handleSort(column.key)}
                      aria-label={getSortAriaLabel(column)}
                    >
                      <span>{column.title}</span>
                      {getSortIcon(column.key)}
                    </button>
                  ) : (
                    column.title
                  )}
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="bg-white divide-y divide-gray-200">
            {data.length === 0 ? (
              <tr>
                <td 
                  colSpan={columns.length} 
                  className="px-6 py-12 text-center text-gray-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((item, index) => (
                <tr 
                  key={item.id || index}
                  className="hover:bg-gray-50 focus-within:bg-gray-50"
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`px-6 py-4 whitespace-nowrap text-sm ${column.className || ''}`}
                    >
                      {column.render 
                        ? column.render(item[column.key], item, index)
                        : item[column.key]
                      }
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default AccessibleTable