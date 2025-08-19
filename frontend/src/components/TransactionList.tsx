/**
 * TransactionList component with search and filtering
 * Displays transaction history with pagination and detailed filtering options
 */
import React, { useState, useEffect, useCallback } from 'react'
import { useAuth } from './AuthGuard'
import LoadingSpinner from './shared/LoadingSpinner'
import AdvancedSearch, { SearchFilters } from './AdvancedSearch'
import SortableTable, { Column, SortConfig } from './SortableTable'
import { transactionsService } from '../services/transactions'
import { accountsService } from '../services/accounts'

interface Transaction {
  id: string
  sender_id: string
  recipient_id: string
  sender_name: string
  recipient_name: string
  amount: string
  transaction_type: string
  status: string
  category?: string
  note?: string
  created_at: string
}

// Remove the old interface since we're using SearchFilters from AdvancedSearch

interface PaginationInfo {
  page: number
  per_page: number
  total: number
  pages: number
}

const TransactionList: React.FC = () => {
  const { user } = useAuth()
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<SearchFilters>({})
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    per_page: 20,
    total: 0,
    pages: 0
  })
  const [categories, setCategories] = useState<string[]>([])

  // Load transaction categories
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await transactionsService.getTransactionCategories()
        setCategories(response.categories.map((cat: any) => cat.name))
      } catch (error) {
        console.error('Failed to load categories:', error)
      }
    }
    loadCategories()
  }, [])

  // Load transactions
  const loadTransactions = useCallback(async (page = 1) => {
    try {
      setLoading(true)
      setError(null)

      const queryParams = {
        page,
        per_page: pagination.per_page,
        ...filters
      }

      const response = await accountsService.getTransactionHistory(queryParams)
      
      setTransactions(response.transactions)
      setPagination({
        page: response.pagination.page,
        per_page: response.pagination.per_page,
        total: response.pagination.total,
        pages: response.pagination.pages
      })
    } catch (error: any) {
      console.error('Failed to load transactions:', error)
      setError(error.message || 'Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }, [filters, pagination.per_page])

  // Load transactions when filters change
  useEffect(() => {
    if (user) {
      loadTransactions(1)
    }
  }, [user, loadTransactions])

  const handleFiltersChange = (newFilters: SearchFilters) => {
    setFilters(newFilters)
  }

  const handleSearch = () => {
    loadTransactions(1)
  }

  const clearFilters = () => {
    setFilters({})
  }

  const handleSort = (sortConfig: SortConfig) => {
    setFilters(prev => ({
      ...prev,
      sortBy: sortConfig.key,
      sortOrder: sortConfig.direction
    }))
  }

  // Define table columns
  const columns: Column<Transaction>[] = [
    {
      key: 'created_at',
      title: 'Date & Time',
      sortable: true,
      render: (value) => formatDate(value)
    },
    {
      key: 'transaction_type',
      title: 'Type',
      sortable: true,
      render: (value, transaction) => (
        <div>
          <div className="text-sm text-gray-900">
            {getTransactionTypeLabel(value)}
          </div>
          {transaction.category && (
            <div className="text-xs text-gray-500">
              {transaction.category}
            </div>
          )}
        </div>
      )
    },
    {
      key: 'counterparty',
      title: 'Counterparty',
      sortable: true,
      render: (_, transaction) => (
        <div className="text-sm text-gray-900">
          {isOutgoing(transaction) ? (
            <>
              <span className="text-red-600">To:</span> {transaction.recipient_name}
            </>
          ) : (
            <>
              <span className="text-green-600">From:</span> {transaction.sender_name}
            </>
          )}
        </div>
      )
    },
    {
      key: 'amount',
      title: 'Amount',
      sortable: true,
      render: (value, transaction) => (
        <div className={`text-sm font-medium ${
          isOutgoing(transaction) ? 'text-red-600' : 'text-green-600'
        }`}>
          {isOutgoing(transaction) ? '-' : '+'}
          {formatCurrency(value)}
        </div>
      )
    },
    {
      key: 'status',
      title: 'Status',
      sortable: true,
      render: (value) => (
        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(value)}`}>
          {value.toLowerCase()}
        </span>
      )
    },
    {
      key: 'note',
      title: 'Note',
      sortable: false,
      className: 'max-w-xs truncate',
      render: (value) => value || '-'
    }
  ]

  const formatCurrency = (amount: string) => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP'
    }).format(parseFloat(amount))
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getTransactionTypeLabel = (type: string) => {
    switch (type) {
      case 'TRANSFER':
        return 'Transfer'
      case 'EVENT_CONTRIBUTION':
        return 'Event Contribution'
      default:
        return type
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'text-green-600 bg-green-100'
      case 'PENDING':
        return 'text-yellow-600 bg-yellow-100'
      case 'FAILED':
        return 'text-red-600 bg-red-100'
      case 'CANCELLED':
        return 'text-gray-600 bg-gray-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const isOutgoing = (transaction: Transaction) => {
    return transaction.sender_id === user?.id
  }

  if (loading && transactions.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="large" message="Loading transactions..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transaction History</h1>
          <p className="text-gray-600">
            {pagination.total > 0 
              ? `Showing ${((pagination.page - 1) * pagination.per_page) + 1}-${Math.min(pagination.page * pagination.per_page, pagination.total)} of ${pagination.total} transactions`
              : 'No transactions found'
            }
          </p>
        </div>
      </div>

      {/* Advanced Search */}
      <AdvancedSearch
        filters={filters}
        onFiltersChange={handleFiltersChange}
        onSearch={handleSearch}
        onClear={clearFilters}
        categories={categories}
        loading={loading}
      />

      {/* Error State */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Transactions</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
              <div className="mt-4">
                <button
                  onClick={() => loadTransactions(pagination.page)}
                  className="bg-red-100 px-2 py-1 text-sm text-red-800 rounded hover:bg-red-200"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Transaction List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading && transactions.length > 0 && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
            <LoadingSpinner size="medium" />
          </div>
        )}

        <SortableTable
          data={transactions}
          columns={columns}
          loading={loading && transactions.length > 0}
          error={error}
          emptyMessage={Object.keys(filters).length > 0 
            ? 'No transactions found matching your filters.'
            : 'You haven\'t made any transactions yet.'
          }
          onSort={handleSort}
          sortConfig={filters.sortBy ? {
            key: filters.sortBy,
            direction: filters.sortOrder || 'desc'
          } : undefined}
        />

        {transactions.length > 0 && (
          <div>
            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => loadTransactions(pagination.page - 1)}
                    disabled={pagination.page <= 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => loadTransactions(pagination.page + 1)}
                    disabled={pagination.page >= pagination.pages}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing{' '}
                      <span className="font-medium">{((pagination.page - 1) * pagination.per_page) + 1}</span>
                      {' '}to{' '}
                      <span className="font-medium">
                        {Math.min(pagination.page * pagination.per_page, pagination.total)}
                      </span>
                      {' '}of{' '}
                      <span className="font-medium">{pagination.total}</span>
                      {' '}results
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => loadTransactions(pagination.page - 1)}
                        disabled={pagination.page <= 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <span className="sr-only">Previous</span>
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>
                      
                      {/* Page numbers */}
                      {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                        const pageNum = Math.max(1, Math.min(pagination.pages - 4, pagination.page - 2)) + i
                        return (
                          <button
                            key={pageNum}
                            onClick={() => loadTransactions(pageNum)}
                            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                              pageNum === pagination.page
                                ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                                : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                            }`}
                          >
                            {pageNum}
                          </button>
                        )
                      })}

                      <button
                        onClick={() => loadTransactions(pagination.page + 1)}
                        disabled={pagination.page >= pagination.pages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <span className="sr-only">Next</span>
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default TransactionList