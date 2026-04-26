export interface Risk {
  id: string
  title: string
  description: string
  category: string
  likelihood: number
  impact: number
  risk_score: number
  status: 'open' | 'mitigated' | 'accepted' | 'closed'
  owner: string
  created_at: string
  updated_at: string
}

export interface RiskCreate {
  title: string
  description?: string
  category?: string
  likelihood: number
  impact: number
  status?: Risk['status']
  owner?: string
}

export interface Control {
  id: string
  control_number: string
  title: string
  domain: string
  applicability: 'applicable' | 'not_applicable'
  implementation_status: 'not_started' | 'in_progress' | 'implemented' | 'verified'
  description: string
  justification: string
  created_at: string
  updated_at: string
}

export interface ControlCreate {
  control_number: string
  title: string
  domain: string
  applicability?: Control['applicability']
  implementation_status?: Control['implementation_status']
  description?: string
  justification?: string
}

export interface Finding {
  id: string
  audit: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  status: 'open' | 'in_remediation' | 'resolved' | 'accepted'
  recommendation: string
  created_at: string
  updated_at: string
}

export interface Audit {
  id: string
  title: string
  scope: string
  auditor: string
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled'
  planned_date: string | null
  completed_date: string | null
  findings: Finding[]
  findings_count: number
  created_at: string
  updated_at: string
}

export interface AuditCreate {
  title: string
  scope?: string
  auditor?: string
  status?: Audit['status']
  planned_date?: string | null
}

export interface HealthStatus {
  status: string
  service: string
}
