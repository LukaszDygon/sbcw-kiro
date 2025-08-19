import '@testing-library/jest-dom'
import 'jest-axe/extend-expect'

// Mock import.meta for Jest
Object.defineProperty(globalThis, 'import', {
  value: {
    meta: {
      env: {
        DEV: true,
        VITE_API_BASE_URL: 'http://localhost:5000/api',
        VITE_MICROSOFT_CLIENT_ID: 'test-client-id',
      }
    }
  }
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() { }
  disconnect() { }
  observe() { }
  unobserve() { }
} as any

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() { }
  disconnect() { }
  observe() { }
  unobserve() { }
} as any

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock speechSynthesis for screen reader detection
Object.defineProperty(window, 'speechSynthesis', {
  writable: true,
  value: {
    speaking: false,
    pending: false,
    paused: false,
    cancel: jest.fn(),
    getVoices: jest.fn(() => []),
    pause: jest.fn(),
    resume: jest.fn(),
    speak: jest.fn(),
  },
})

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock services
jest.mock('./services/auth')
jest.mock('./services/accounts')
jest.mock('./services/transactions')
jest.mock('./services/moneyRequests')
jest.mock('./services/events')

// Mock AuthGuard to prevent infinite loops in tests
jest.mock('./components/AuthGuard')