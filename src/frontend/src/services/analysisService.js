import axios from 'axios'

const DEFAULT_API_BASE_URL = 'http://localhost:8000'
const DEFAULT_USER_ID = 'web-client'

const baseURL = (import.meta.env.API_URL || DEFAULT_API_BASE_URL).replace(/\/+$/, '')

const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const submitScraperRequest = async (link, options = {}) => {
  if (!link) {
    throw new Error('A profile URL is required before starting an analysis.')
  }

  const payload = {
    url: link,
    user_id: DEFAULT_USER_ID,
    ...options,
  }

  try {
    const { data } = await apiClient.post('/v1/scrape', payload)
    return data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const backendMessage = error.response?.data?.detail || error.response?.data?.message
      const statusCode = error.response?.status
      const errorMessage = backendMessage
        || (statusCode ? `Request failed with status ${statusCode}` : 'Failed to reach BellFlow API.')

      throw new Error(errorMessage)
    }

    throw error
  }
}

export default submitScraperRequest
