import client from './client'
import type { HealthStatus } from '@/types'

export const healthApi = {
  check(): Promise<HealthStatus> {
    return client.get<HealthStatus>('/health').then((r) => r.data)
  },
}
