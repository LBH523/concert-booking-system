import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'

const client = axios.create({
  baseURL: API_BASE_URL,
})

// Automatically attach Session-ID if present
client.interceptors.request.use(
  (config) => {
    const sessionId = localStorage.getItem('session_id')
    if (sessionId) {
      config.headers['Session-ID'] = sessionId
    }
    return config
  },
  (error) => Promise.reject(error)
)

export default client
