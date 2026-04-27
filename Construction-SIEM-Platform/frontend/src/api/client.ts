import axios from 'axios'

const client = axios.create({ baseURL: '/api/v1' })

let isRefreshing = false
let pendingQueue: Array<{
  resolve: (token: string) => void
  reject: (err: unknown) => void
}> = []

function processQueue(err: unknown, token: string | null = null) {
  pendingQueue.forEach((p) => {
    if (err) p.reject(err)
    else p.resolve(token!)
  })
  pendingQueue = []
}

client.interceptors.request.use(
  (config) => {
    const t = localStorage.getItem('auth_token')
    if (t && config.headers) {
      config.headers.Authorization = `Bearer ${t}`
    }
    return config
  },
  (err) => Promise.reject(err),
)

client.interceptors.response.use(
  (r) => r,
  async (err) => {
    const original = err.config
    if (
      err.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes('/auth/')
    ) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          pendingQueue.push({ resolve, reject })
        }).then((newToken) => {
          original.headers.Authorization = `Bearer ${newToken}`
          return client(original)
        })
      }
      original._retry = true
      isRefreshing = true
      const storedRefresh = localStorage.getItem('auth_refresh')
      if (storedRefresh) {
        try {
          const res = await axios.post('/api/v1/auth/refresh', {
            refresh_token: storedRefresh,
          })
          const { access_token, refresh_token } = res.data
          localStorage.setItem('auth_token', access_token)
          localStorage.setItem('auth_refresh', refresh_token)
          processQueue(null, access_token)
          original.headers.Authorization = `Bearer ${access_token}`
          return client(original)
        } catch (refreshErr) {
          processQueue(refreshErr, null)
          localStorage.removeItem('auth_token')
          localStorage.removeItem('auth_refresh')
          window.location.href = '/login'
          return Promise.reject(refreshErr)
        } finally {
          isRefreshing = false
        }
      }
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_refresh')
      window.location.href = '/login'
      return Promise.reject(err)
    }
    const msg = err.response?.data?.detail ?? err.message ?? 'Unknown error'
    return Promise.reject(new Error(msg))
  },
)

export default client
