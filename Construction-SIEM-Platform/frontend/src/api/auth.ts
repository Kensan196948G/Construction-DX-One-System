import client from './client'
import type { TokenResponse } from '@/types'

export const authApi = {
  login(username: string, password: string): Promise<TokenResponse> {
    return client
      .post<TokenResponse>('/auth/login', { username, password })
      .then((r) => r.data)
  },

  refresh(refreshToken: string): Promise<TokenResponse> {
    return client
      .post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken })
      .then((r) => r.data)
  },

  logout(): Promise<void> {
    return client.post('/auth/logout').then(() => undefined)
  },
}
