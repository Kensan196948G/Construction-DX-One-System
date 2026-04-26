import axios from 'axios'

const client = axios.create({ baseURL: '/api/v1' })

client.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg =
      err.response?.data?.error?.message ??
      err.response?.data?.detail ??
      err.message ??
      'Unknown error'
    return Promise.reject(new Error(msg))
  },
)

export default client
