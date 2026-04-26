import type { Control, ControlCreate } from '@/types'
import client from './client'

export const complianceApi = {
  list(implementation_status?: string, applicability?: string): Promise<Control[]> {
    const params: Record<string, string> = {}
    if (implementation_status) params.implementation_status = implementation_status
    if (applicability) params.applicability = applicability
    return client.get<Control[]>('/compliance/', { params }).then((r) => r.data)
  },

  get(id: string): Promise<Control> {
    return client.get<Control>(`/compliance/${id}/`).then((r) => r.data)
  },

  create(data: ControlCreate): Promise<Control> {
    return client.post<Control>('/compliance/', data).then((r) => r.data)
  },

  update(id: string, data: ControlCreate): Promise<Control> {
    return client.put<Control>(`/compliance/${id}/`, data).then((r) => r.data)
  },

  delete(id: string): Promise<void> {
    return client.delete(`/compliance/${id}/`).then(() => undefined)
  },
}
