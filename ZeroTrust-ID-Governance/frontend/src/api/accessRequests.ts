import client from './client'
import type { AccessRequest, AccessRequestCreate, RequestReview } from '@/types'

export const accessRequestsApi = {
  list(status?: string, limit = 50, offset = 0): Promise<AccessRequest[]> {
    return client
      .get<AccessRequest[]>('/access-requests', { params: { status, limit, offset } })
      .then((r) => r.data)
  },

  get(id: string): Promise<AccessRequest> {
    return client.get<AccessRequest>(`/access-requests/${id}`).then((r) => r.data)
  },

  create(data: AccessRequestCreate): Promise<AccessRequest> {
    return client.post<AccessRequest>('/access-requests', data).then((r) => r.data)
  },

  approve(id: string, data: RequestReview = {}): Promise<AccessRequest> {
    return client.post<AccessRequest>(`/access-requests/${id}/approve`, data).then((r) => r.data)
  },

  reject(id: string, data: RequestReview = {}): Promise<AccessRequest> {
    return client.post<AccessRequest>(`/access-requests/${id}/reject`, data).then((r) => r.data)
  },

  cancel(id: string): Promise<AccessRequest> {
    return client.post<AccessRequest>(`/access-requests/${id}/cancel`).then((r) => r.data)
  },
}
