import client from './client'
import type { User, UserCreate, UserStatusUpdate, UserType, UserStatus } from '@/types'

export const usersApi = {
  list(userType?: UserType, status?: UserStatus, limit = 50, offset = 0): Promise<User[]> {
    return client
      .get<User[]>('/users', { params: { user_type: userType, status, limit, offset } })
      .then((r) => r.data)
  },

  get(id: string): Promise<User> {
    return client.get<User>(`/users/${id}`).then((r) => r.data)
  },

  create(data: UserCreate): Promise<User> {
    return client.post<User>('/users', data).then((r) => r.data)
  },

  updateStatus(id: string, data: UserStatusUpdate): Promise<User> {
    return client.patch<User>(`/users/${id}/status`, data).then((r) => r.data)
  },

  delete(id: string): Promise<void> {
    return client.delete(`/users/${id}`).then(() => undefined)
  },
}
