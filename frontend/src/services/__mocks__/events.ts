// Mock events service for testing
const mockEventsService = {
  createEvent: jest.fn().mockResolvedValue({ success: true, event: { id: 'test-event' } }),
  contributeToEvent: jest.fn().mockResolvedValue({ success: true }),
  getActiveEvents: jest.fn().mockResolvedValue({ events: [] }),
  getEventById: jest.fn().mockResolvedValue(null),
  getEventContributions: jest.fn().mockResolvedValue({ contributions: [] }),
  closeEvent: jest.fn().mockResolvedValue({ success: true }),
}

export const eventsService = mockEventsService
export default mockEventsService

// Also export individual functions for backward compatibility
export const createEvent = mockEventsService.createEvent
export const contributeToEvent = mockEventsService.contributeToEvent
export const getActiveEvents = mockEventsService.getActiveEvents
export const getEventById = mockEventsService.getEventById
export const getEventContributions = mockEventsService.getEventContributions
export const closeEvent = mockEventsService.closeEvent