import client from './client'
import type { Incident, IncidentCreate, IncidentStatusUpdate, IncidentSeverity, IncidentStatus } from '@/types'

interface ListResponse<T> {
  data: T[]
  pagination: { total_count: number; has_next: boolean }
}

export const incidentsApi = {
  list(status?: IncidentStatus, severity?: IncidentSeverity, limit = 50): Promise<Incident[]> {
    return client
      .get<ListResponse<Incident>>('/incidents', { params: { status, severity, limit } })
      .then((r) => r.data.data)
  },

  get(id: string): Promise<Incident> {
    return client.get<{ data: Incident }>(`/incidents/${id}`).then((r) => r.data.data)
  },

  create(data: IncidentCreate): Promise<Incident> {
    return client.post<{ data: Incident }>('/incidents', data).then((r) => r.data.data)
  },

  updateStatus(id: string, data: IncidentStatusUpdate): Promise<Incident> {
    return client.patch<{ data: Incident }>(`/incidents/${id}/status`, data).then((r) => r.data.data)
  },
}
