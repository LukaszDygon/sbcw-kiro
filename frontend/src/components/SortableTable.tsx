/**
 * SortableTable component for displaying data with sorting capabilities
 * Provides consistent table UI with sorting, pagination, and loading states
 */
import React, { useState } from 'react'

export interface Column<T> {
  key: keyof T | string
  title: string
  sortable?: boolean
  render?: (value: any, item: T, index: number) => React.ReactNode
  className?: string
  headerClassName?: string
}

export interface SortConfig {
  key: string
  direction: 'asc' | 'desc'
}

interface SortableTableProps<T> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  error?: string | null
  emptyMessage?: string
  onSort?: (sortConfig: SortConfig) => void
  sortConfig?: SortConfig
  className?: string
  rowClassName?: (item: T, index: number) => string
  onRowClick?: (item: T, index: number) => void
}

function SortableTable<T extends Record<string, any>>({
  data,
  columns,
  loading = false,
  error = null,
  emptyMessage = 'No data available',
  onSort,
  sortConfig,
  className = '',
  rowClassName,
  onRowClick
}: SortableTableProps<T>) {
  const [internalSortConfig, setInternalSortConfig] = useState<SortConfig | null>(null)
  
  const currentSortConfig = sortConfig || internalSortConfig

  const handleSort = (columnKey: string) => {
    const column = columns.find(col => col.key === columnKey)
    if (!column?.sortable) return

    let direction: 'asc' | 'desc' = 'asc'
    
    if (currentSortConfig?.key === columnKey && currentSortConfig.direction === 'asc') {
      direction = 'desc'
    }

    const newSortConfig = { key: columnKey, direction }
    
    if (onSort) {
      onSort(newSortConfig)
    } else {
      setInternalSortConfig(newSortConfig)
    }
  }

  const getSortedData = () => {
    if (!currentSortConfig || onSort) {
      // If external sorting is handled or no sort config, return data as-is
      return data
    }

    return [...data].sort((a, b) => {
      const aValue = a[currentSortConfig.key]
      const bValue = b[currentSortConfig.key]
      
      // Handle null/undefined values
      if (aValue == null && bValue == null) return 0
      if (aValue == null) return 1
      if (bValue == null) return -1
      
      // Handle different data types
      let comparison = 0
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        comparison = aValue.localeCompare(bValue)
      } else if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue
      } else if (aValue instanceof Date && bValue instanceof Date) {
        comparison = aValue.getTime() - bValue.getTime()
      } else {
        // Fallback to string comparison
        comparison = String(aValue).localeCompare(String(bValue))
      }
      
      return currentSortConfig.direction === 'desc' ? -comparison : comparison
    })
  }

  const getSortIcon = (columnKey: string) => {
    if (currentSortConfig?.key !== columnKey) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      )
    }
    
    if (currentSortConfig.direction === 'asc') {
      return (
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
        </svg>
      )
    } else {
      return (
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
        </svg>
      )
    }
  }

  const getValue = (item: T, key: keyof T | string): any => {
    if (typeof key === 'string' && key.includes('.')) {
      // Handle nested keys like 'user.name'
      return key.split('.').reduce((obj, k) => obj?.[k], item)
    }
    return item[key as keyof T]
  }

  const sortedData = getSortedData()

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Data</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`bg-white shadow rounded-lg overflow-hidden ${className}`}>
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
          <div className="flex items-center space-x-2">
            <svg className="animate-spin h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm text-gray-600">Loading...</span>
          </div>
        </div>
      )}

      {sortedData.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map((column, index) => (
                  <th
                    key={String(column.key)}
                    className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                      column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                    } ${column.headerClassName || ''}`}
                    onClick={() => column.sortable && handleSort(String(column.key))}
                  >
                    <div className="flex items-center space-x-1">
                      <span>{column.title}</span>
                      {column.sortable && getSortIcon(String(column.key))}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedData.map((item, index) => (
                <tr
                  key={index}
                  className={`hover:bg-gray-50 ${
                    onRowClick ? 'cursor-pointer' : ''
                  } ${rowClassName ? rowClassName(item, index) : ''}`}
                  onClick={() => onRowClick?.(item, index)}
                >
                  {columns.map((column) => (
                    <td
                      key={String(column.key)}
                      className={`px-6 py-4 whitespace-nowrap text-sm ${column.className || ''}`}
                    >
                      {column.render
                        ? column.render(getValue(item, column.key), item, index)
                        : getValue(item, column.key) || '-'
                      }
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No Data</h3>
          <p className="mt-1 text-sm text-gray-500">{emptyMessage}</p>
        </div>
      )}
    </div>
  )
}

export default SortableTable