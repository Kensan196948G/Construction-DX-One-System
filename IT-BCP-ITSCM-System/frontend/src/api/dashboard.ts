import client from './client'
import type { DashboardRtoOverview, DashboardActiveIncidents } from '@/types'

export const dashboardApi = {
  rtoOverview(): Promise<DashboardRtoOverview> {
    return client.get<DashboardRtoOverview>('/dashboard/rto-overview').then((r) => r.data)
  },

  activeIncidentsSummary(): Promise<DashboardActiveIncidents> {
    return client
      .get<DashboardActiveIncidents>('/dashboard/active-incidents-summary')
      .then((r) => r.data)
  },
}
