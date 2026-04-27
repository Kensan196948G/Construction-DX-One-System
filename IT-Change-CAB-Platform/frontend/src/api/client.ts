import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'

const client = axios.create({ baseURL: '/api/v1' })

let isRefreshing = false
let pendingQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function getAccessToken(): string | null {
  return localStorage.getItem('accessToken')
}
function getRefreshToken(): string | null {
  return localStorage.getItem('refreshToken')
}
function clearTokens() {
  localStorage.removeItem('accessToken')
  localStorage.removeItem('refreshToken')
}
function setTokens(access: string, refresh?: string) {
  localStorage.setItem('accessToken', access)
  if (refresh) localStorage.setItem('refreshToken', refresh)
}

client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (r) => r,
  async (err: AxiosError) => {
    const originalRequest = err.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    if (err.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          pendingQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return client(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = getRefreshToken()
        if (!refreshToken) throw new Error('No refresh token')

        const res = await axios.post('/api/v1/auth/refresh', { refreshToken })
        const { accessToken, refreshToken: newRefresh } = res.data
        setTokens(accessToken, newRefresh)

        pendingQueue.forEach((p) => p.resolve(accessToken))
        pendingQueue = []

        originalRequest.headers.Authorization = `Bearer ${accessToken}`
        return client(originalRequest)
      } catch {
        pendingQueue.forEach((p) => p.reject(err))
        pendingQueue = []
        clearTokens()
        window.location.href = '/login'
        return Promise.reject(err)
      } finally {
        isRefreshing = false
      }
    }

    const data = err.response?.data as Record<string, any> | undefined
    const msg =
      data?.error?.message ??
      data?.detail ??
      err.message ??
      'Unknown error'
    return Promise.reject(new Error(msg))
  },
)

export default client
