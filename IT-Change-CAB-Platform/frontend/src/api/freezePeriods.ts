import client from './client'

export interface FreezePeriodCreate {
  title: string
  start_date: string
  end_date: string
  reason?: string
}

export interface FreezePeriod {
  id: string
  title: string
  start_date: string
  end_date: string
  reason?: string | null
  created_at?: string
}

export const freezePeriodsApi = {
  list: (): Promise<FreezePeriod[]> =>
    client.get('/api/v1/freeze-periods').then((r) => r.data),

  create: (data: FreezePeriodCreate): Promise<FreezePeriod> =>
    client.post('/api/v1/freeze-periods', data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    client.delete(`/api/v1/freeze-periods/${id}`).then((r) => r.data),
}
