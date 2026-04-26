import client from './client'
import type { Rfc, RfcCreate, RfcStatusUpdate, RfcStatus, ChangeType, ChangePriority } from '@/types'

interface RfcListResponse {
  data: Rfc[]
  meta: { page: number; limit: number; total: number; totalPages: number }
}

export const rfcsApi = {
  list(status?: RfcStatus, changeType?: ChangeType, priority?: ChangePriority, limit = 50): Promise<Rfc[]> {
    return client
      .get<RfcListResponse>('/rfcs', { params: { status, change_type: changeType, priority, limit } })
      .then((r) => r.data.data)
  },

  get(id: string): Promise<Rfc> {
    return client.get<{ data: Rfc }>(`/rfcs/${id}`).then((r) => r.data.data)
  },

  create(data: RfcCreate): Promise<Rfc> {
    return client.post<{ data: Rfc }>('/rfcs', data).then((r) => r.data.data)
  },

  updateStatus(id: string, data: RfcStatusUpdate): Promise<Rfc> {
    return client.patch<{ data: Rfc }>(`/rfcs/${id}/status`, data).then((r) => r.data.data)
  },
}
