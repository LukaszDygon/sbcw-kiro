// Mock transactions service
const mockTransactionsService = {
  getCategories: jest.fn().mockResolvedValue({
    categories: [
      { id: '1', name: 'Food' },
      { id: '2', name: 'Transport' }
    ]
  }),
  sendMoney: jest.fn().mockResolvedValue({
    id: 'trans-123',
    amount: '25.00',
    recipient_name: 'John Doe',
    sender_name: 'Test User',
    note: 'Test payment',
    created_at: '2024-01-15T12:00:00Z',
    status: 'COMPLETED',
    transaction_type: 'TRANSFER'
  }),
  sendBulkMoney: jest.fn(),
  getRecentTransactions: jest.fn().mockResolvedValue({
    transactions: [],
    count: 0
  }),
  getTransactionHistory: jest.fn(),
  validateTransaction: jest.fn(),
  exportTransactions: jest.fn(),
};

export const transactionsService = mockTransactionsService;
export default mockTransactionsService;

// Also export individual functions for backward compatibility
export const getCategories = mockTransactionsService.getCategories;
export const sendMoney = mockTransactionsService.sendMoney;
export const sendBulkMoney = mockTransactionsService.sendBulkMoney;
export const getRecentTransactions = mockTransactionsService.getRecentTransactions;
export const getTransactionHistory = mockTransactionsService.getTransactionHistory;
export const validateTransaction = mockTransactionsService.validateTransaction;
export const exportTransactions = mockTransactionsService.exportTransactions;