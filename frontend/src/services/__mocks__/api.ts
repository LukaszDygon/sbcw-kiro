// Mock API client for testing
export const API_BASE_URL = 'http://localhost:5000/api'

class MockApiClient {
  async get(url: string) {
    return { data: {}, status: 200 }
  }

  async post(url: string, data?: any) {
    return { data: {}, status: 200 }
  }

  async put(url: string, data?: any) {
    return { data: {}, status: 200 }
  }

  async delete(url: string) {
    return { data: {}, status: 200 }
  }

  setAuthToken(token: string) {
    // Mock implementation
  }

  clearAuthToken() {
    // Mock implementation
  }
}

const apiClient = new MockApiClient()

export default apiClient

export const handleApiError = (error: any) => {
  console.error('API Error:', error)
  throw error
}