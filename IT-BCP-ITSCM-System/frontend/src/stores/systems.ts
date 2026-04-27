import { defineStore } from 'pinia'
import { ref } from 'vue'
import { systemsApi } from '@/api/systems'
import type { ItSystem, SystemTier, SystemStatus } from '@/types'

export const useSystemsStore = defineStore('systems', () => {
  const systems = ref<ItSystem[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchSystems(tier?: SystemTier, status?: SystemStatus) {
    loading.value = true
    error.value = null
    try {
      systems.value = await systemsApi.list(tier, status)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load systems'
    } finally {
      loading.value = false
    }
  }

  const tier1Systems = () => systems.value.filter((s) => s.tier === 'tier1')
  const degradedSystems = () => systems.value.filter((s) => s.status === 'degraded' || s.status === 'down')

  return {
    systems,
    loading,
    error,
    fetchSystems,
    tier1Systems,
    degradedSystems,
  }
})
