import client from './client'
import type { LoginRequest, LoginResponse, RefreshResponse } from '@/types'

export const authApi = {
  login(data: LoginRequest): Promise<LoginResponse> {
    return client.post<LoginResponse>('/auth/login', data).then((r) => r.data)
  },
  refresh(refreshToken: string): Promise<RefreshResponse> {
    return client.post<RefreshResponse>('/auth/refresh', { refreshToken }).then((r) => r.data)
  },
  logout(): Promise<void> {
    return client.post('/auth/logout').then(() => {})
  },
}
