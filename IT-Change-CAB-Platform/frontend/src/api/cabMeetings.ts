import client from './client'
import type { CabMeeting, CabStatus } from '@/types'

interface CabListResponse {
  data: CabMeeting[]
  meta: { page: number; limit: number; total: number; totalPages: number }
}

export const cabMeetingsApi = {
  list(status?: CabStatus, limit = 20): Promise<CabMeeting[]> {
    return client
      .get<CabListResponse>('/cab/meetings', { params: { status, limit } })
      .then((r) => r.data.data)
  },

  get(id: string): Promise<CabMeeting> {
    return client.get<{ data: CabMeeting }>(`/cab/meetings/${id}`).then((r) => r.data.data)
  },
}
