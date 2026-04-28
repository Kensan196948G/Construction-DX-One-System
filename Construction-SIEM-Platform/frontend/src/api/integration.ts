import axios from 'axios'

const INTEGRATION_KEY =
  import.meta.env.VITE_INTEGRATION_KEY ?? 'dev-integration-key-change-in-prod'

const integrationClient = axios.create({
  baseURL: '/api/v1/integration',
  headers: { 'X-Integration-Key': INTEGRATION_KEY },
})

export interface AlertSummary {
  total_open: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  generated_at: string
}

export interface PendingIncident {
  id: string
  title: string
  severity: string
  status: string
  detected_at: string
}

export interface EscalateResult {
  escalated: boolean
  rfc_reference: string
  incident_id: string
}

export const integrationApi = {
  getAlertSummary(): Promise<AlertSummary> {
    return integrationClient.get<AlertSummary>('/alerts/summary').then((r) => r.data)
  },

  getPendingIncidents(): Promise<PendingIncident[]> {
    return integrationClient.get<PendingIncident[]>('/incidents/pending').then((r) => r.data)
  },

  escalateToCAB(
    incidentId: string,
    requestedBy: string,
    changeReason: string,
  ): Promise<EscalateResult> {
    return integrationClient
      .post<EscalateResult>(`/incidents/${incidentId}/escalate-to-cab`, {
        incident_id: incidentId,
        requested_by: requestedBy,
        change_reason: changeReason,
      })
      .then((r) => r.data)
  },
}
