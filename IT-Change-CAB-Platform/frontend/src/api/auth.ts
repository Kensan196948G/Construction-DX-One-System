import client from './client'
import type { LoginRequest, LoginResponse, TokenRefreshResponse } from '@/types'

export const authApi = {
  login(data: LoginRequest): Promise<LoginResponse> {
    return client.post<LoginResponse>('/auth/login', data).then((r) => r.data)
  },
  refresh(refreshToken: string): Promise<TokenRefreshResponse> {
    return client
      .post<TokenRefreshResponse>('/auth/refresh', { refreshToken })
      .then((r) => r.data)
  },
  logout(): Promise<void> {
    return client.post('/auth/logout').then(() => undefined)
  },
}
