import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      const rt = localStorage.getItem('refresh_token')
      if (rt) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: rt })
          localStorage.setItem('access_token', data.access_token)
          if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
          error.config.headers.Authorization = `Bearer ${data.access_token}`
          return apiClient(error.config)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    const message = error.response?.data?.detail ?? error.message ?? 'Unknown error'
    return Promise.reject(new Error(message))
  },
)

export default apiClient
