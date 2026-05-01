import client from './client'
import type { BiaRecord, ImpactLevel } from '@/types'

export interface BiaCreateInput {
  system_id: string
  assessment_date: string
  rto_hours: number
  rpo_hours: number
  impact_level: ImpactLevel
  notes?: string
}

export const biaApi = {
  list: (): Promise<BiaRecord[]> => client.get('/bia').then((r) => r.data),
  create: (data: BiaCreateInput): Promise<BiaRecord> =>
    client.post('/bia', data).then((r) => r.data),
}
