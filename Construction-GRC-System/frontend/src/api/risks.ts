import type { Risk, RiskCreate } from '@/types'
import client from './client'

export const risksApi = {
  list(status?: string): Promise<Risk[]> {
    const params = status ? { status } : {}
    return client.get<Risk[]>('/risks/', { params }).then((r) => r.data)
  },

  get(id: string): Promise<Risk> {
    return client.get<Risk>(`/risks/${id}/`).then((r) => r.data)
  },

  create(data: RiskCreate): Promise<Risk> {
    return client.post<Risk>('/risks/', data).then((r) => r.data)
  },

  update(id: string, data: RiskCreate): Promise<Risk> {
    return client.put<Risk>(`/risks/${id}/`, data).then((r) => r.data)
  },

  delete(id: string): Promise<void> {
    return client.delete(`/risks/${id}/`).then(() => undefined)
  },
}
