import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRulesStore } from '@/stores/rules'
import { rulesApi } from '@/api/rules'
import type { Rule } from '@/types'

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

const mockRule: Rule = {
  id: 'rule1',
  rule_id: 'CSIEM-001',
  name: 'Brute Force Detection',
  description: 'Detects brute force login attempts',
  rule_type: 'custom',
  rule_content: 'login_failures > 5',
  severity: 'high',
  category: 'authentication',
  is_active: true,
  mitre_attack_id: 'T1110',
  match_count: 42,
  last_matched_at: '2026-04-27T10:00:00Z',
  created_at: '2026-04-01T00:00:00Z',
  updated_at: '2026-04-27T00:00:00Z',
}

const inactiveRule: Rule = {
  ...mockRule,
  id: 'rule2',
  rule_id: 'CSIEM-002',
  name: 'SQL Injection',
  severity: 'critical',
  is_active: false,
}

describe('useRulesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchRules sets rules on success', async () => {
    vi.mocked(rulesApi.list).mockResolvedValueOnce([mockRule, inactiveRule])
    const store = useRulesStore()
    await store.fetchRules()

    expect(store.rules).toHaveLength(2)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchRules passes active filters', async () => {
    vi.mocked(rulesApi.list).mockResolvedValueOnce([mockRule])
    const store = useRulesStore()
    store.setFilter('severity', 'high')
    store.setFilter('category', 'authentication')
    await store.fetchRules()

    expect(rulesApi.list).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'high', category: 'authentication' }),
    )
  })

  it('fetchRules sets error on failure', async () => {
    vi.mocked(rulesApi.list).mockRejectedValueOnce(new Error('API error'))
    const store = useRulesStore()
    await store.fetchRules()

    expect(store.rules).toHaveLength(0)
    expect(store.error).toBe('API error')
    expect(store.loading).toBe(false)
  })

  it('createRule prepends to rules list', async () => {
    vi.mocked(rulesApi.create).mockResolvedValueOnce(mockRule)
    const store = useRulesStore()
    const result = await store.createRule({
      name: 'Brute Force Detection',
      rule_type: 'custom',
      rule_content: 'login_failures > 5',
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
      rule_type: 'custom',
      rule_content: '',
      severity: 'low',
      category: '',
    })

    expect(result).toBeNull()
    expect(store.error).toBe('Validation error')
  })

  it('updateRule replaces rule in list', async () => {
    const updated = { ...mockRule, name: 'Updated Brute Force' }
    vi.mocked(rulesApi.update).mockResolvedValueOnce(updated)
    const store = useRulesStore()
    store.rules = [mockRule]

    const result = await store.updateRule('rule1', { name: 'Updated Brute Force' })
    expect(result?.name).toBe('Updated Brute Force')
    expect(store.rules[0].name).toBe('Updated Brute Force')
  })

  it('deleteRule removes rule from list', async () => {
    vi.mocked(rulesApi.delete).mockResolvedValueOnce(undefined)
    const store = useRulesStore()
    store.rules = [mockRule, inactiveRule]

    const result = await store.deleteRule('rule1')
    expect(result).toBe(true)
    expect(store.rules).toHaveLength(1)
    expect(store.rules[0].id).toBe('rule2')
  })

  it('deleteRule returns false on failure', async () => {
    vi.mocked(rulesApi.delete).mockRejectedValueOnce(new Error('Cannot delete'))
    const store = useRulesStore()
    const result = await store.deleteRule('rule1')

    expect(result).toBe(false)
    expect(store.error).toBe('Cannot delete')
  })

  it('toggleRule updates is_active in list', async () => {
    const toggled = { ...mockRule, is_active: false }
    vi.mocked(rulesApi.toggle).mockResolvedValueOnce(toggled)
    const store = useRulesStore()
    store.rules = [mockRule]

    const result = await store.toggleRule('rule1')
    expect(result?.is_active).toBe(false)
    expect(store.rules[0].is_active).toBe(false)
  })

  it('testRule stores test result', async () => {
    const testResult = { matched: true, details: 'Rule matched event' }
    vi.mocked(rulesApi.test).mockResolvedValueOnce(testResult)
    const store = useRulesStore()

    const result = await store.testRule({ rule_content: 'login_failures > 5', rule_type: 'custom', event_data: {} })
    expect(result).toEqual(testResult)
    expect(store.testResult).toEqual(testResult)
  })

  it('testRule returns null on failure and clears result', async () => {
    vi.mocked(rulesApi.test).mockRejectedValueOnce(new Error('Test failed'))
    const store = useRulesStore()
    store.testResult = { matched: true, details: null }

    const result = await store.testRule({ rule_content: 'bad', rule_type: 'custom', event_data: {} })
    expect(result).toBeNull()
    expect(store.testResult).toBeNull()
  })

  it('fetchStats stores stats summary', async () => {
    const statsData = { by_severity: { high: 3 }, by_category: { auth: 2 }, total_active: 5, total_inactive: 2 }
    vi.mocked(rulesApi.stats).mockResolvedValueOnce(statsData)
    const store = useRulesStore()
    await store.fetchStats()

    expect(store.stats).toEqual(statsData)
  })

  it('clearTestResult resets to null', () => {
    const store = useRulesStore()
    store.testResult = { matched: false, details: 'no match' }
    store.clearTestResult()
    expect(store.testResult).toBeNull()
  })

  it('activeRules computed returns only active rules', async () => {
    vi.mocked(rulesApi.list).mockResolvedValueOnce([mockRule, inactiveRule])
    const store = useRulesStore()
    await store.fetchRules()

    expect(store.activeRules).toHaveLength(1)
    expect(store.activeRules[0].is_active).toBe(true)
  })

  it('inactiveRules computed returns only inactive rules', async () => {
    vi.mocked(rulesApi.list).mockResolvedValueOnce([mockRule, inactiveRule])
    const store = useRulesStore()
    await store.fetchRules()

    expect(store.inactiveRules).toHaveLength(1)
    expect(store.inactiveRules[0].is_active).toBe(false)
  })

  it('bySeverity groups rules by severity', async () => {
    vi.mocked(rulesApi.list).mockResolvedValueOnce([mockRule, inactiveRule])
    const store = useRulesStore()
    await store.fetchRules()

    expect(store.bySeverity['high']).toHaveLength(1)
    expect(store.bySeverity['critical']).toHaveLength(1)
  })

  it('setFilter updates filter values', () => {
    const store = useRulesStore()
    store.setFilter('rule_type', 'sigma')
    expect(store.filters.rule_type).toBe('sigma')
  })
})
