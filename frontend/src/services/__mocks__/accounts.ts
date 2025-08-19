// Mock accounts service for testing
const mockAccountsService = {
    getBalance: jest.fn().mockResolvedValue({
        balance: '150.00',
        available_balance: '150.00',
        currency: 'GBP',
        limits: {
            minimum_balance: '-250.00',
            maximum_balance: '250.00',
            overdraft_limit: '250.00'
        }
    }),
    searchUsers: jest.fn().mockResolvedValue({ users: [] }),
    validateTransaction: jest.fn().mockResolvedValue({ valid: true }),
    getAccountSummary: jest.fn().mockResolvedValue({
        account_id: 'test-account',
        user_id: 'test-user',
        current_balance: '0.00',
        available_balance: '0.00',
        currency: 'GBP',
        account_limits: {
            minimum_balance: '0.00',
            maximum_balance: '10000.00',
            overdraft_limit: '500.00'
        },
        recent_activity: {
            period_days: 30,
            total_sent: '0.00',
            total_received: '0.00',
            transaction_count: 0
        }
    }),
    getSpendingAnalytics: jest.fn().mockResolvedValue({
        period_days: 30,
        start_date: '2024-01-01',
        end_date: '2024-01-31',
        total_spent: '0.00',
        total_transactions: 0,
        average_transaction: '0.00',
        categories: []
    }),
    getAccountStatus: jest.fn().mockResolvedValue({ status: 'ACTIVE' }),
}

export const accountsService = mockAccountsService
export default mockAccountsService

// Also export individual functions for backward compatibility
export const getBalance = mockAccountsService.getBalance
export const searchUsers = mockAccountsService.searchUsers
export const validateTransaction = mockAccountsService.validateTransaction
export const getAccountSummary = mockAccountsService.getAccountSummary
export const getSpendingAnalytics = mockAccountsService.getSpendingAnalytics
export const getAccountStatus = mockAccountsService.getAccountStatus