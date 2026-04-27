export type UserType = 'employee' | 'contractor' | 'partner' | 'admin'
export type UserStatus = 'active' | 'disabled' | 'locked'
export type RequestStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'expired'
  | 'cancelled'
  | 'in_review'

export interface User {
  id: string
  username: string
  email: string
  full_name: string
  user_type: UserType
  status: UserStatus
  department: string | null
  created_at: string
  last_login_at: string | null
  mfa_enabled: boolean
  risk_score: number
}

export interface UserCreate {
  username: string
  email: string
  full_name: string
  user_type?: UserType
  department?: string | null
  mfa_enabled?: boolean
}

export interface UserStatusUpdate {
  status: UserStatus
}

export interface AccessRequest {
  id: string
  requester_id: string
  requester_name: string
  requested_role: string
  resource: string | null
  reason: string
  status: RequestStatus
  created_at: string
  reviewed_at: string | null
  reviewed_by: string | null
  expires_at: string | null
}

export interface AccessRequestCreate {
  requested_role: string
  resource?: string | null
  reason: string
  expires_at?: string | null
}

export interface RequestReview {
  comment?: string | null
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
  role?: string
}

export interface Role {
  id: string
  name: string
  description: string | null
  permissions: string[]
  is_privileged: boolean
  created_at: string
}

export interface RoleCreate {
  name: string
  description?: string | null
  permissions?: string[]
  is_privileged?: boolean
}

export interface RoleUpdate {
  name?: string
  description?: string | null
  permissions?: string[]
  is_privileged?: boolean
}

export interface RoleAssign {
  user_id: string
  expires_at?: string | null
}
