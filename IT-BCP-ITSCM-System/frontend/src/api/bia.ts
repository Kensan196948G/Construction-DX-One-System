import client from './client'

export interface BiaCreateInput {
  system_id: string
  assessment_date: string
  rto_hours: number
  rpo_hours: number
  impact_level: string
  notes?: string
}

export const biaApi = {
  list: (): Promise<any[]> => client.get('/bia').then((r) => r.data),
  create: (data: BiaCreateInput): Promise<any> =>
    client.post('/bia', data).then((r) => r.data),
}
