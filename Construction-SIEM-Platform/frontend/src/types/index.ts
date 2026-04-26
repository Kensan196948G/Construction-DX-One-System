export type EventSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical'
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical'
export type AlertStatus = 'open' | 'investigating' | 'resolved' | 'false_positive'

export interface SecurityEvent {
  id: string
  event_type: string
  severity: EventSeverity
  source_ip: string | null
  source_hostname: string | null
  destination_ip: string | null
  destination_port: number | null
  occurred_at: string
  ingested_at: string
  raw_log: string | null
  log_source: string | null
  risk_score: number
  correlation_id: string | null
  is_processed: boolean
}

export interface SecurityEventCreate {
  event_type: string
  severity?: EventSeverity
  source_ip?: string | null
  source_hostname?: string | null
  destination_ip?: string | null
  destination_port?: number | null
  occurred_at?: string
  raw_log?: string | null
  log_source?: string | null
  risk_score?: number
  correlation_id?: string | null
}

export interface Alert {
  id: string
  title: string
  description: string | null
  severity: AlertSeverity
  status: AlertStatus
  risk_score: number
  event_count: number
  rule_name: string | null
  correlation_id: string | null
  assigned_to: string | null
  mitre_technique: string | null
  mitre_tactic: string | null
  detected_at: string
  resolved_at: string | null
}

export interface AlertCreate {
  title: string
  description?: string | null
  severity?: AlertSeverity
  risk_score?: number
  event_count?: number
  rule_name?: string | null
  correlation_id?: string | null
  assigned_to?: string | null
  mitre_technique?: string | null
  mitre_tactic?: string | null
}

export interface AlertStatusUpdate {
  status: AlertStatus
  assigned_to?: string | null
}

export interface HealthStatus {
  status: string
  service: string
}

export function severityWeight(s: EventSeverity | AlertSeverity): number {
  const map: Record<string, number> = { info: 0, low: 1, medium: 2, high: 3, critical: 4 }
  return map[s] ?? 0
}
