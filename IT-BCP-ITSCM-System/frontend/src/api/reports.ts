import client from './client'

export const reportsApi = {
  getExecutiveSummary: (): Promise<any> =>
    client.get('/reports/executive-summary').then((r) => r.data),
  getSystemStatus: (): Promise<any> =>
    client.get('/reports/system-status').then((r) => r.data),
}
