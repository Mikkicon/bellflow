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

      const requestError = new Error(errorMessage)
      if (typeof statusCode === 'number') {
        requestError.status = statusCode
      }

      throw requestError
    }

    throw error
  }
}

export const fetchTaskStatus = async (taskId) => {
  if (!taskId) {
    throw new Error('A task ID is required before retrieving task status.')
  }

  try {
    const { data } = await apiClient.get(`/v1/tasks/${taskId}`)
    return data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const backendMessage = error.response?.data?.detail || error.response?.data?.message
      const statusCode = error.response?.status
      const errorMessage = backendMessage
        || (statusCode ? `Request failed with status ${statusCode}` : 'Failed to reach BellFlow API.')

      const requestError = new Error(errorMessage)
      if (typeof statusCode === 'number') {
        requestError.status = statusCode
      }

      throw requestError
    }

    throw error
  }
}

export default submitScraperRequest