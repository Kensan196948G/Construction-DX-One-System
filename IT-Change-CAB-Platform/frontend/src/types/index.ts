export type ChangeType = 'normal' | 'emergency' | 'standard'
export type ChangePriority = 'low' | 'medium' | 'high' | 'critical'
export type TechnicalRisk = 'low' | 'medium' | 'high'
export type RfcStatus =
  | 'draft'
  | 'pending_approval'
  | 'cab_review'
  | 'approved'
  | 'rejected'
  | 'in_progress'
  | 'completed'
  | 'cancelled'

export type CabStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled'

export interface RfcRequester {
  id: string
  displayName: string
}

export interface Rfc {
  id: string
  rfcNumber: string
  title: string
  description: string | null
  changeType: ChangeType
  priority: ChangePriority
  status: RfcStatus
  targetSystems: string[]
  affectedUsers: number
  plannedStart: string
  plannedEnd: string
  businessImpact: string | null
  technicalRisk: TechnicalRisk
  riskScore: number
  rollbackPlan: string | null
  requester: RfcRequester
  createdAt: string
  updatedAt: string
}

export interface RfcCreate {
  title: string
  description?: string | null
  changeType: ChangeType
  priority: ChangePriority
  targetSystems: string[]
  affectedUsers?: number
  plannedStart: string
  plannedEnd: string
  businessImpact?: string | null
  technicalRisk: TechnicalRisk
  rollbackPlan?: string | null
}

export interface RfcStatusUpdate {
  status: RfcStatus
  comment?: string | null
}

export interface CabMeeting {
  id: string
  meetingNumber: string
  title: string
  status: CabStatus
  scheduledAt: string
  facilitator: string | null
  rfcCount: number
  createdAt: string
}

export interface HealthStatus {
  status: string
  service: string
}

export interface AuthUser {
  id: string
  username: string
  displayName: string
  roles: string[]
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  refreshToken: string
  user: AuthUser
}

export interface TokenRefreshResponse {
  accessToken: string
  refreshToken?: string
}
