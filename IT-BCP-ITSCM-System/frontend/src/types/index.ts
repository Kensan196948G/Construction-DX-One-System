export type IncidentSeverity = 'critical' | 'high' | 'medium' | 'low'
export type IncidentStatus =
  | 'open'
  | 'investigating'
  | 'bcp_activated'
  | 'recovering'
  | 'resolved'
  | 'closed'

export type SystemTier = 'tier1' | 'tier2' | 'tier3' | 'tier4'
export type SystemStatus = 'normal' | 'degraded' | 'down' | 'maintenance'

export type ExerciseType = 'tabletop' | 'functional' | 'full_scale' | 'drill'
export type ExerciseStatus = 'planned' | 'in_progress' | 'completed' | 'cancelled'

export interface Incident {
  id: string
  incidentNumber: string
  title: string
  description: string | null
  severity: IncidentSeverity
  status: IncidentStatus
  affectedSystemsCount: number
  bcpActivated: boolean
  declaredAt: string | null
  resolvedAt: string | null
  createdAt: string
  updatedAt: string
}

export interface IncidentCreate {
  title: string
  description?: string | null
  severity: IncidentSeverity
  affectedSystemIds?: string[]
}

export interface IncidentStatusUpdate {
  status: IncidentStatus
  comment?: string | null
}

export interface ItSystem {
  id: string
  systemName: string
  description: string | null
  tier: SystemTier
  status: SystemStatus
  rtoMinutes: number
  rpoMinutes: number
  recoveryPriority: number
  owner: string | null
  createdAt: string
  updatedAt: string
}

export interface Exercise {
  id: string
  exerciseNumber: string
  title: string
  type: ExerciseType
  status: ExerciseStatus
  scheduledAt: string
  completedAt: string | null
  scenarioTitle: string | null
  participantsCount: number
  createdAt: string
}

export interface DashboardRtoOverview {
  totalSystems: number
  systemsMeetingRto: number
  systemsBreachingRto: number
  averageRtoMinutes: number
}

export interface DashboardActiveIncidents {
  total: number
  critical: number
  high: number
  bcpActivated: number
}

export interface HealthStatus {
  status: string
  service: string
}

export interface User {
  id: string
  username: string
  email?: string
  displayName?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  refreshToken: string
  user: User
}

export interface RefreshResponse {
  accessToken: string
}
