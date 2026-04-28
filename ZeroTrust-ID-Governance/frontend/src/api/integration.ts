import axios from 'axios'

const INTEGRATION_KEY =
  import.meta.env.VITE_INTEGRATION_KEY ?? 'dev-integration-key-change-in-prod'

const integrationClient = axios.create({
  baseURL: '/api/v1/integration',
  headers: { 'X-Integration-Key': INTEGRATION_KEY },
})

export interface IdentitySummary {
  total_users: number
  active_users: number
  privileged_users: number
  generated_at: string
}

export interface AuthEvent {
  id: string
  event_type: string
  username: string
  actor_ip: string
  severity: string
  timestamp: string
}

export interface AuthEventsResponse {
  events: AuthEvent[]
  total_count: number
  period_hours: number
}

export const integrationApi = {
  getIdentitySummary(): Promise<IdentitySummary> {
    return integrationClient.get<IdentitySummary>('/identity-summary').then((r) => r.data)
  },

  getRecentAuthEvents(hours = 1): Promise<AuthEventsResponse> {
    return integrationClient
      .get<AuthEventsResponse>('/auth-events/recent', { params: { hours } })
      .then((r) => r.data)
  },

  sendWebhookNotify(event: string, source: string): Promise<void> {
    return integrationClient
      .post('/webhook/notify', { event, source })
      .then(() => undefined)
  },
}
