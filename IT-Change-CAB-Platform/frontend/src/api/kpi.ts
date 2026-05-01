import client from './client'

export interface KpiDashboard {
  change_success_rate?: number | null
  total_changes?: number | null
  successful_changes?: number | null
  failed_changes?: number | null
  avg_lead_time_days?: number | null
  pending_approvals?: number | null
  open_rfcs?: number | null
  emergency_changes?: number | null
  cab_meetings_this_month?: number | null
  [key: string]: unknown
}

export const kpiApi = {
  getDashboard: (): Promise<KpiDashboard> =>
    client.get('/api/v1/kpi').then((r) => r.data),
}
