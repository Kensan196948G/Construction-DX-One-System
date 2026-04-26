import client from './client'
import type { Alert, AlertCreate, AlertStatusUpdate, AlertStatus, AlertSeverity } from '@/types'

export const alertsApi = {
  list(status?: AlertStatus, severity?: AlertSeverity, limit = 50, offset = 0): Promise<Alert[]> {
    return client
      .get<Alert[]>('/alerts', { params: { status, severity, limit, offset } })
      .then((r) => r.data)
  },

  get(id: string): Promise<Alert> {
    return client.get<Alert>(`/alerts/${id}`).then((r) => r.data)
  },

  create(data: AlertCreate): Promise<Alert> {
    return client.post<Alert>('/alerts', data).then((r) => r.data)
  },

  updateStatus(id: string, data: AlertStatusUpdate): Promise<Alert> {
    return client.patch<Alert>(`/alerts/${id}/status`, data).then((r) => r.data)
  },
}
