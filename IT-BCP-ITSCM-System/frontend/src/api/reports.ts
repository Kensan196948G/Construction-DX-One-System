import client from './client'
import type { ExecutiveSummary, SystemStatusReport } from '@/types'

export const reportsApi = {
  getExecutiveSummary: (): Promise<ExecutiveSummary> =>
    client.get('/reports/executive-summary').then((r) => r.data),
  getSystemStatus: (): Promise<SystemStatusReport> =>
    client.get('/reports/system-status').then((r) => r.data),
}
