import { defineStore } from 'pinia'
import { ref } from 'vue'
import { risksApi } from '@/api/risks'
import type { Risk, RiskCreate } from '@/types'

export const useRisksStore = defineStore('risks', () => {
  const risks = ref<Risk[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchRisks(status?: string) {
    loading.value = true
    error.value = null
    try {
      risks.value = await risksApi.list(status)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load risks'
    } finally {
      loading.value = false
    }
  }

  async function createRisk(data: RiskCreate): Promise<Risk | null> {
    try {
      const risk = await risksApi.create(data)
      risks.value.unshift(risk)
      return risk
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create risk'
      return null
    }
  }

  async function updateRisk(id: string, data: RiskCreate): Promise<boolean> {
    try {
      const updated = await risksApi.update(id, data)
      const idx = risks.value.findIndex((r) => r.id === id)
      if (idx !== -1) risks.value[idx] = updated
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update risk'
      return false
    }
  }

  async function deleteRisk(id: string): Promise<boolean> {
    try {
      await risksApi.delete(id)
      risks.value = risks.value.filter((r) => r.id !== id)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete risk'
      return false
    }
  }

  const openRisks = () => risks.value.filter((r) => r.status === 'open')
  const highRisks = () => risks.value.filter((r) => r.risk_score >= 15)

  return { risks, loading, error, fetchRisks, createRisk, updateRisk, deleteRisk, openRisks, highRisks }
})
