import client from './client'
import type { Role, RoleCreate, RoleUpdate, RoleAssign } from '@/types'

export const rolesApi = {
  list(): Promise<Role[]> {
    return client.get<Role[]>('/roles').then((r) => r.data)
  },

  get(id: string): Promise<Role> {
    return client.get<Role>(`/roles/${id}`).then((r) => r.data)
  },

  create(data: RoleCreate): Promise<Role> {
    return client.post<Role>('/roles', data).then((r) => r.data)
  },

  update(id: string, data: RoleUpdate): Promise<Role> {
    return client.put<Role>(`/roles/${id}`, data).then((r) => r.data)
  },

  delete(id: string): Promise<void> {
    return client.delete(`/roles/${id}`).then(() => undefined)
  },

  assign(roleId: string, data: RoleAssign): Promise<Role> {
    return client.post<Role>(`/roles/${roleId}/assign`, data).then((r) => r.data)
  },

  revoke(roleId: string, userId: string): Promise<void> {
    return client.delete(`/roles/${roleId}/revoke/${userId}`).then(() => undefined)
  },
}
