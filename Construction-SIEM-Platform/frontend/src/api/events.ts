import client from './client'
import type { SecurityEvent, SecurityEventCreate, EventSeverity } from '@/types'

export const eventsApi = {
  list(severity?: EventSeverity, limit = 50, offset = 0): Promise<SecurityEvent[]> {
    return client
      .get<SecurityEvent[]>('/events', { params: { severity, limit, offset } })
      .then((r) => r.data)
  },

  get(id: string): Promise<SecurityEvent> {
    return client.get<SecurityEvent>(`/events/${id}`).then((r) => r.data)
  },

  ingest(data: SecurityEventCreate): Promise<SecurityEvent> {
    return client.post<SecurityEvent>('/events', data).then((r) => r.data)
  },

  bulkIngest(data: SecurityEventCreate[]): Promise<SecurityEvent[]> {
    return client.post<SecurityEvent[]>('/events/bulk', data).then((r) => r.data)
  },

  markProcessed(id: string): Promise<SecurityEvent> {
    return client.patch<SecurityEvent>(`/events/${id}/processed`).then((r) => r.data)
  },
}
