import client from './client'
import type { ItSystem, SystemTier, SystemStatus } from '@/types'

interface ListResponse<T> {
  data: T[]
  pagination: { total_count: number; has_next: boolean }
}

export const systemsApi = {
  list(tier?: SystemTier, status?: SystemStatus, limit = 50): Promise<ItSystem[]> {
    return client
      .get<ListResponse<ItSystem>>('/systems', { params: { tier, status, limit } })
      .then((r) => r.data.data)
  },

  get(id: string): Promise<ItSystem> {
    return client.get<{ data: ItSystem }>(`/systems/${id}`).then((r) => r.data.data)
  },
}
