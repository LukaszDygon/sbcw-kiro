// Mock money requests service for testing
const mockMoneyRequestsService = {
  createMoneyRequest: jest.fn().mockResolvedValue({ success: true, request: { id: 'test-req' } }),
  approveMoneyRequest: jest.fn().mockResolvedValue({ success: true }),
  declineMoneyRequest: jest.fn().mockResolvedValue({ success: true }),
  getPendingRequests: jest.fn().mockResolvedValue({ requests: [] }),
  getSentRequests: jest.fn().mockResolvedValue({ requests: [] }),
  getReceivedRequests: jest.fn().mockResolvedValue({ requests: [] }),
}

export const moneyRequestsService = mockMoneyRequestsService
export default mockMoneyRequestsService

// Also export individual functions for backward compatibility
export const createMoneyRequest = mockMoneyRequestsService.createMoneyRequest
export const approveMoneyRequest = mockMoneyRequestsService.approveMoneyRequest
export const declineMoneyRequest = mockMoneyRequestsService.declineMoneyRequest
export const getPendingRequests = mockMoneyRequestsService.getPendingRequests
export const getSentRequests = mockMoneyRequestsService.getSentRequests
export const getReceivedRequests = mockMoneyRequestsService.getReceivedRequests