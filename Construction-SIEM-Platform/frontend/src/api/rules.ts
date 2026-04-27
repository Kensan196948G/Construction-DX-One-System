import client from './client'
import type {
  Rule,
  RuleCreate,
  RuleUpdate,
  RuleTestRequest,
  RuleTestResult,
  RuleStatsSummary,
  RuleSeverity,
  RuleType,
} from '@/types'

export interface RuleListParams {
  severity?: RuleSeverity
  category?: string
  rule_type?: RuleType
  is_active?: boolean
  limit?: number
  offset?: number
}

export const rulesApi = {
  list(params?: RuleListParams): Promise<Rule[]> {
    return client.get<Rule[]>('/rules', { params }).then((r) => r.data)
  },

  get(id: string): Promise<Rule> {
    return client.get<Rule>(`/rules/${id}`).then((r) => r.data)
  },

  create(data: RuleCreate): Promise<Rule> {
    return client.post<Rule>('/rules', data).then((r) => r.data)
  },

  update(id: string, data: RuleUpdate): Promise<Rule> {
    return client.put<Rule>(`/rules/${id}`, data).then((r) => r.data)
  },

  delete(id: string): Promise<void> {
    return client.delete(`/rules/${id}`).then(() => undefined)
  },

  toggle(id: string): Promise<Rule> {
    return client.post<Rule>(`/rules/${id}/toggle`).then((r) => r.data)
  },

  test(data: RuleTestRequest): Promise<RuleTestResult> {
    return client.post<RuleTestResult>('/rules/test', data).then((r) => r.data)
  },

  stats(): Promise<RuleStatsSummary> {
    return client.get<RuleStatsSummary>('/rules/stats/summary').then((r) => r.data)
  },
}
