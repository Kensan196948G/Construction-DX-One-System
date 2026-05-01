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

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuthUser {
  username: string
  role: string
}

export function severityWeight(s: EventSeverity | AlertSeverity): number {
  const map: Record<string, number> = { info: 0, low: 1, medium: 2, high: 3, critical: 4 }
  return map[s] ?? 0
}

export type RuleSeverity = 'low' | 'medium' | 'high' | 'critical'
export type RuleType = 'sigma' | 'yara' | 'custom'

export interface Rule {
  id: string
  rule_id: string
  name: string
  description: string | null
  rule_type: RuleType
  rule_content: string
  severity: RuleSeverity
  category: string
  is_active: boolean
  mitre_attack_id: string | null
  match_count: number
  last_matched_at: string | null
  created_at: string
  updated_at: string
}

export interface RuleCreate {
  name: string
  description?: string | null
  rule_type: RuleType
  rule_content: string
  severity: RuleSeverity
  category: string
  mitre_attack_id?: string | null
}

export interface RuleUpdate {
  name?: string
  description?: string | null
  rule_type?: RuleType
  rule_content?: string
  severity?: RuleSeverity
  category?: string
  is_active?: boolean
  mitre_attack_id?: string | null
}

export interface RuleTestRequest {
  rule_content: string
  rule_type: RuleType
  event_data: Record<string, unknown>
}

export interface RuleTestResult {
  matched: boolean
  details: string | null
}

export interface RuleStatsSummary {
  by_severity: Record<string, number>
  by_category: Record<string, number>
  total_active: number
  total_inactive: number
}

export type IoCType = 'ip' | 'domain' | 'url' | 'hash' | 'email' | string

export interface IoCMatchDetail {
  ioc_value: string
  ioc_type: string
  threat_type: string
  confidence: number
  severity: string
  description: string
  source: string
  first_seen: string
  last_seen: string
}

export interface IoCCheckRequest {
  value: string
  ioc_type: IoCType
}

export interface IoCCheckResponse {
  status: string
  ioc_value: string
  ioc_type: string
  malicious: boolean
  matches: IoCMatchDetail[]
  risk_score: number
}

export interface CorrelateEventMatch {
  field: string
  value: string
  ioc_type: string
  match: IoCMatchDetail
}

export interface CorrelateEventRequest {
  event_data: Record<string, unknown>
}

export interface CorrelateEventResponse {
  status: string
  matches: CorrelateEventMatch[]
  total_matches: number
  risk_score: number
}

export interface RecentThreatItem {
  ioc_value: string
  ioc_type: string
  threat_type: string
  confidence: number
  severity: string
  last_seen: string
}

export interface RecentThreatsResponse {
  status: string
  data: RecentThreatItem[]
}
