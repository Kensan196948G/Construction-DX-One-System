import type { HealthStatus } from '@/types'
import client from './client'

export const healthApi = {
  check(): Promise<HealthStatus> {
    return client.get<HealthStatus>('/health/').then((r) => r.data)
  },
}
