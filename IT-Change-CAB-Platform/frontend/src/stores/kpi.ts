import { defineStore } from 'pinia'
import { ref } from 'vue'
import { kpiApi } from '@/api/kpi'
import type { KpiDashboard } from '@/api/kpi'

export const useKpiStore = defineStore('kpi', () => {
  const kpiData = ref<KpiDashboard | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchKpi(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      kpiData.value = await kpiApi.getDashboard()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load KPI data'
    } finally {
      loading.value = false
    }
  }

  return {
    kpiData,
    loading,
    error,
    fetchKpi,
  }
})
