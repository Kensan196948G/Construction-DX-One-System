import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { rulesApi } from '@/api/rules'
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

export const useRulesStore = defineStore('rules', () => {
  const rules = ref<Rule[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const stats = ref<RuleStatsSummary | null>(null)
  const testResult = ref<RuleTestResult | null>(null)

  const filters = ref({
    severity: '' as RuleSeverity | '',
    category: '',
    rule_type: '' as RuleType | '',
    is_active: '' as boolean | '',
  })

  const activeRules = computed(() => rules.value.filter((r) => r.is_active))
  const inactiveRules = computed(() => rules.value.filter((r) => !r.is_active))

  const bySeverity = computed(() => {
    const map: Record<string, Rule[]> = {}
    for (const r of rules.value) {
      if (!map[r.severity]) map[r.severity] = []
      map[r.severity].push(r)
    }
    return map
  })

  const recentRules = computed(() =>
    [...rules.value].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    ).slice(0, 10),
  )

  async function fetchRules() {
    loading.value = true
    error.value = null
    try {
      const params: Record<string, unknown> = {}
      if (filters.value.severity) params.severity = filters.value.severity
      if (filters.value.category) params.category = filters.value.category
      if (filters.value.rule_type) params.rule_type = filters.value.rule_type
      if (filters.value.is_active !== '') params.is_active = filters.value.is_active
      rules.value = await rulesApi.list(params)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load rules'
    } finally {
      loading.value = false
    }
  }

  async function createRule(data: RuleCreate): Promise<Rule | null> {
    try {
      const rule = await rulesApi.create(data)
      rules.value.unshift(rule)
      return rule
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create rule'
      return null
    }
  }

  async function updateRule(id: string, data: RuleUpdate): Promise<Rule | null> {
    try {
      const updated = await rulesApi.update(id, data)
      const idx = rules.value.findIndex((r) => r.id === id)
      if (idx !== -1) rules.value.splice(idx, 1, updated)
      return updated
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update rule'
      return null
    }
  }

  async function deleteRule(id: string): Promise<boolean> {
    try {
      await rulesApi.delete(id)
      rules.value = rules.value.filter((r) => r.id !== id)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete rule'
      return false
    }
  }

  async function toggleRule(id: string): Promise<Rule | null> {
    try {
      const updated = await rulesApi.toggle(id)
      const idx = rules.value.findIndex((r) => r.id === id)
      if (idx !== -1) rules.value.splice(idx, 1, updated)
      return updated
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to toggle rule'
      return null
    }
  }

  async function testRule(data: RuleTestRequest): Promise<RuleTestResult | null> {
    try {
      const result = await rulesApi.test(data)
      testResult.value = result
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Test failed'
      testResult.value = null
      return null
    }
  }

  async function fetchStats() {
    try {
      stats.value = await rulesApi.stats()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load stats'
    }
  }

  function setFilter<K extends keyof typeof filters.value>(
    key: K,
    value: (typeof filters.value)[K],
  ) {
    filters.value[key] = value
  }

  function clearTestResult() {
    testResult.value = null
  }

  return {
    rules,
    loading,
    error,
    stats,
    testResult,
    filters,
    activeRules,
    inactiveRules,
    bySeverity,
    recentRules,
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
    toggleRule,
    testRule,
    fetchStats,
    setFilter,
    clearTestResult,
  }
})
