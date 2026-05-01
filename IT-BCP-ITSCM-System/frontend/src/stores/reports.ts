import { defineStore } from 'pinia'
import { ref } from 'vue'
import { reportsApi } from '@/api/reports'

export const useReportsStore = defineStore('reports', () => {
  const executiveSummary = ref<any | null>(null)
  const systemStatus = ref<any | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchExecutiveSummary() {
    loading.value = true
    error.value = null
    try {
      executiveSummary.value = await reportsApi.getExecutiveSummary()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load executive summary'
    } finally {
      loading.value = false
    }
  }

  async function fetchSystemStatus() {
    loading.value = true
    error.value = null
    try {
      systemStatus.value = await reportsApi.getSystemStatus()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load system status'
    } finally {
      loading.value = false
    }
  }

  return {
    executiveSummary,
    systemStatus,
    loading,
    error,
    fetchExecutiveSummary,
    fetchSystemStatus,
  }
})
