import client from './client'
import type {
  IoCCheckRequest,
  IoCCheckResponse,
  CorrelateEventRequest,
  CorrelateEventResponse,
  RecentThreatsResponse,
} from '@/types'

export const threatIntelApi = {
  check(payload: IoCCheckRequest): Promise<IoCCheckResponse> {
    return client.post<IoCCheckResponse>('/threat-intel/check', payload).then((r) => r.data)
  },

  correlate(payload: CorrelateEventRequest): Promise<CorrelateEventResponse> {
    return client
      .post<CorrelateEventResponse>('/threat-intel/correlate', payload)
      .then((r) => r.data)
  },

  recent(hours = 24): Promise<RecentThreatsResponse> {
    return client
      .get<RecentThreatsResponse>('/threat-intel/recent', { params: { hours } })
      .then((r) => r.data)
  },
}
