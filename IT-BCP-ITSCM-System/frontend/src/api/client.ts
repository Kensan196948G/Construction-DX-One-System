import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

let isRefreshing = false
let pendingQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function onRefreshed(token: string) {
  for (const p of pendingQueue) p.resolve(token)
  pendingQueue = []
}

function onRefreshFailed(err: unknown) {
  for (const p of pendingQueue) p.reject(err)
  pendingQueue = []
}

function getStoredAuth(): { accessToken?: string; refreshToken?: string } | null {
  try {
    const raw = localStorage.getItem('auth')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function setAccessToken(token: string) {
  const auth = getStoredAuth()
  if (!auth) return
  auth.accessToken = token
  localStorage.setItem('auth', JSON.stringify(auth))
}

function clearAuth() {
  localStorage.removeItem('auth')
}

client.interceptors.request.use((config) => {
  const auth = getStoredAuth()
  if (auth?.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

client.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config

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
        const auth = getStoredAuth()
        if (!auth?.refreshToken) throw new Error('No refresh token')

        const res = await axios.post('/api/v1/auth/refresh', {
          refreshToken: auth.refreshToken,
        })
        const { accessToken } = res.data
        setAccessToken(accessToken)
        onRefreshed(accessToken)
        originalRequest.headers.Authorization = `Bearer ${accessToken}`
        return client(originalRequest)
      } catch (refreshErr) {
        onRefreshFailed(refreshErr)
        clearAuth()
        window.location.href = '/login'
        return Promise.reject(refreshErr)
      } finally {
        isRefreshing = false
      }
    }

    const msg =
      err.response?.data?.detail ??
      err.response?.data?.message ??
      err.message ??
      'Unknown error'
    return Promise.reject(new Error(msg))
  },
)

export default client
