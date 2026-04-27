import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRulesStore } from '@/stores/rules'
import { rulesApi } from '@/api/rules'

vi.mock('@/api/rules', () => ({
  rulesApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    toggle: vi.fn(),
    test: vi.fn(),
    stats: vi.fn(),
  },
}))

const mockRule = {
  id: 'rule-1',
  rule_id: 'SIGMA-001',
  name: '不審なログイン検知',
  description: '短時間での複数回ログイン失敗を検知',
  rule_type: 'sigma' as const,
  rule_content: 'detection: ...',
  severity: 'high' as const,
  category: 'authentication',
  is_active: true,
  mitre_attack_id: 'T1110',
  match_count: 5,
  last_matched_at: '2026-04-25T09:00:00Z',
  created_at: '2026-04-01T00:00:00Z',
  updated_at: '2026-04-25T09:00:00Z',
}

const mockInactiveRule = {
  ...mockRule,
  id: 'rule-2',
  rule_id: 'SIGMA-002',
  name: 'ポートスキャン検知',
  severity: 'medium' as const,
  category: 'network',
  is_active: false,
  created_at: '2026-04-02T00:00:00Z',
}

describe('useRulesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initial state: empty rules, no loading, no error', () => {
    const store = useRulesStore()
    expect(store.rules).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.stats).toBeNull()
    expect(store.testResult).toBeNull()
  })

  it('fetchRules sets rules on success', async () => {
    vi.mocked(rulesApi.list).mockResolvedValueOnce([mockRule, mockInactiveRule])
    const store = useRulesStore()
    await store.fetchRules()
    expect(store.rules).toHaveLength(2)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchRules with filters passes params to API', async () => {
    vi.mocked(rulesApi.list).mockResolvedValueOnce([mockRule])
    const store = useRulesStore()
    store.filters.severity = 'high'
    store.filters.category = 'authentication'
    await store.fetchRules()
    expect(rulesApi.list).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'high', category: 'authentication' }),
    )
  })

  it('fetchRules skips empty filters', async () => {
    vi.mocked(rulesApi.list).mockResolvedValueOnce([])
    const store = useRulesStore()
    await store.fetchRules()
    expect(rulesApi.list).toHaveBeenCalledWith({})
  })

  it('fetchRules sets error on failure', async () => {
    vi.mocked(rulesApi.list).mockRejectedValueOnce(new Error('Connection refused'))
    const store = useRulesStore()
    await store.fetchRules()
    expect(store.rules).toHaveLength(0)
    expect(store.error).toBe('Connection refused')
    expect(store.loading).toBe(false)
  })

  it('createRule prepends to rules list', async () => {
    vi.mocked(rulesApi.create).mockResolvedValueOnce(mockRule)
    const store = useRulesStore()
    const result = await store.createRule({
      name: '不審なログイン検知',
      rule_type: 'sigma',
      rule_content: 'detection: ...',
      severity: 'high',
      category: 'authentication',
    })
    expect(result).toEqual(mockRule)
    expect(store.rules[0]).toEqual(mockRule)
  })

  it('createRule returns null on failure', async () => {
    vi.mocked(rulesApi.create).mockRejectedValueOnce(new Error('Validation error'))
    const store = useRulesStore()
    const result = await store.createRule({
      name: '',
      rule_type: 'sigma',
      rule_content: '',
      severity: 'low',
      category: '',
    })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation error')
  })

  it('updateRule replaces rule in list', async () => {
    const updated = { ...mockRule, name: '強化版ログイン検知' }
    vi.mocked(rulesApi.update).mockResolvedValueOnce(updated)
    const store = useRulesStore()
    store.rules = [mockRule]
    const result = await store.updateRule('rule-1', { name: '強化版ログイン検知' })
    expect(result).toEqual(updated)
    expect(store.rules[0].name).toBe('強化版ログイン検知')
  })

  it('updateRule returns null on failure', async () => {
    vi.mocked(rulesApi.update).mockRejectedValueOnce(new Error('Rule not found'))
    const store = useRulesStore()
    const result = await store.updateRule('nonexistent', { name: '' })
    expect(result).toBeNull()
    expect(store.error).toBe('Rule not found')
  })

  it('deleteRule removes rule from list', async () => {
    vi.mocked(rulesApi.delete).mockResolvedValueOnce(undefined)
    const store = useRulesStore()
    store.rules = [mockRule, mockInactiveRule]
    const result = await store.deleteRule('rule-1')
    expect(result).toBe(true)
    expect(store.rules).toHaveLength(1)
    expect(store.rules[0].id).toBe('rule-2')
  })

  it('deleteRule returns false on failure', async () => {
    vi.mocked(rulesApi.delete).mockRejectedValueOnce(new Error('Cannot delete active rule'))
    const store = useRulesStore()
    const result = await store.deleteRule('rule-1')
    expect(result).toBe(false)
    expect(store.error).toBe('Cannot delete active rule')
  })

  it('toggleRule updates rule is_active in list', async () => {
    const toggled = { ...mockRule, is_active: false }
    vi.mocked(rulesApi.toggle).mockResolvedValueOnce(toggled)
    const store = useRulesStore()
    store.rules = [mockRule]
    const result = await store.toggleRule('rule-1')
    expect(result).toEqual(toggled)
    expect(store.rules[0].is_active).toBe(false)
  })

  it('toggleRule returns null on failure', async () => {
    vi.mocked(rulesApi.toggle).mockRejectedValueOnce(new Error('Toggle failed'))
    const store = useRulesStore()
    const result = await store.toggleRule('nonexistent')
    expect(result).toBeNull()
    expect(store.error).toBe('Toggle failed')
  })

  it('testRule sets testResult on success', async () => {
    const testResult = { matched: true, details: 'Pattern matched at line 3' }
    vi.mocked(rulesApi.test).mockResolvedValueOnce(testResult)
    const store = useRulesStore()
    const result = await store.testRule({
      rule_content: 'detection: ...',
      rule_type: 'sigma',
      event_data: { EventID: 4625 },
    })
    expect(result).toEqual(testResult)
    expect(store.testResult).toEqual(testResult)
  })

  it('testRule returns null and clears testResult on failure', async () => {
    vi.mocked(rulesApi.test).mockRejectedValueOnce(new Error('Parse error'))
    const store = useRulesStore()
    store.testResult = { matched: false, details: null }
    const result = await store.testRule({
      rule_content: 'invalid',
      rule_type: 'sigma',
      event_data: {},
    })
    expect(result).toBeNull()
    expect(store.testResult).toBeNull()
    expect(store.error).toBe('Parse error')
  })

  it('fetchStats sets stats on success', async () => {
    const mockStats = {
      by_severity: { high: 3, medium: 2, low: 1, critical: 0 },
      by_category: { authentication: 4, network: 2 },
      total_active: 5,
      total_inactive: 1,
    }
    vi.mocked(rulesApi.stats).mockResolvedValueOnce(mockStats)
    const store = useRulesStore()
    await store.fetchStats()
    expect(store.stats).toEqual(mockStats)
  })

  it('fetchStats sets error on failure', async () => {
    vi.mocked(rulesApi.stats).mockRejectedValueOnce(new Error('Stats unavailable'))
    const store = useRulesStore()
    await store.fetchStats()
    expect(store.stats).toBeNull()
    expect(store.error).toBe('Stats unavailable')
  })

  it('setFilter updates filter values', () => {
    const store = useRulesStore()
    store.setFilter('severity', 'critical')
    store.setFilter('category', 'network')
    store.setFilter('rule_type', 'yara')
    expect(store.filters.severity).toBe('critical')
    expect(store.filters.category).toBe('network')
    expect(store.filters.rule_type).toBe('yara')
  })

  it('clearTestResult sets testResult to null', () => {
    const store = useRulesStore()
    store.testResult = { matched: true, details: 'found' }
    store.clearTestResult()
    expect(store.testResult).toBeNull()
  })

  it('activeRules computed returns only active rules', () => {
    const store = useRulesStore()
    store.rules = [mockRule, mockInactiveRule]
    expect(store.activeRules).toHaveLength(1)
    expect(store.activeRules[0].id).toBe('rule-1')
  })

  it('inactiveRules computed returns only inactive rules', () => {
    const store = useRulesStore()
    store.rules = [mockRule, mockInactiveRule]
    expect(store.inactiveRules).toHaveLength(1)
    expect(store.inactiveRules[0].id).toBe('rule-2')
  })

  it('bySeverity computed groups rules by severity', () => {
    const store = useRulesStore()
    store.rules = [mockRule, mockInactiveRule]
    expect(store.bySeverity['high']).toHaveLength(1)
    expect(store.bySeverity['medium']).toHaveLength(1)
  })

  it('recentRules computed returns up to 10 sorted by created_at desc', () => {
    const store = useRulesStore()
    store.rules = [mockRule, mockInactiveRule]
    const recent = store.recentRules
    expect(recent).toHaveLength(2)
    expect(new Date(recent[0].created_at).getTime()).toBeGreaterThanOrEqual(
      new Date(recent[1].created_at).getTime(),
    )
  })
})
