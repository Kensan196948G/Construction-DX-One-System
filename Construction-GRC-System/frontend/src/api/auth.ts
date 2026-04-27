import apiClient from './client'
import type { LoginResponse, RefreshResponse, User } from '@/types'

export const authApi = {
  login(username: string, password: string): Promise<LoginResponse> {
    return apiClient.post('/auth/login', { username, password }).then((r) => r.data)
  },

  refresh(refreshToken: string): Promise<RefreshResponse> {
    return apiClient.post('/auth/refresh', { refresh_token: refreshToken }).then((r) => r.data)
  },

  logout(refreshToken: string): Promise<void> {
    return apiClient.post('/auth/logout', { refresh_token: refreshToken })
  },

  me(): Promise<User> {
    return apiClient.get('/auth/me').then((r) => r.data)
  },
}
