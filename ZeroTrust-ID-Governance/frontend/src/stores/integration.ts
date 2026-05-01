import { defineStore } from 'pinia'
import { ref } from 'vue'
import { integrationApi } from '@/api/integration'
import type { IdentitySummary, AuthEventsResponse } from '@/api/integration'

export const useIntegrationStore = defineStore('integration', () => {
  const identitySummary = ref<IdentitySummary | null>(null)
  const authEvents = ref<AuthEventsResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const periodHours = ref(1)

  async function fetchIdentitySummary() {
    loading.value = true
    error.value = null
    try {
      identitySummary.value = await integrationApi.getIdentitySummary()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load identity summary'
    } finally {
      loading.value = false
    }
  }

  async function fetchAuthEvents(hours = 1) {
    loading.value = true
    error.value = null
    periodHours.value = hours
    try {
      authEvents.value = await integrationApi.getRecentAuthEvents(hours)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load auth events'
    } finally {
      loading.value = false
    }
  }

  return { identitySummary, authEvents, loading, error, periodHours, fetchIdentitySummary, fetchAuthEvents }
})
