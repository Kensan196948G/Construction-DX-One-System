import { defineStore } from 'pinia'
import { ref } from 'vue'
import { integrationApi } from '@/api/integration'
import type { AlertSummary, PendingIncident } from '@/api/integration'

export const useIntegrationStore = defineStore('integration', () => {
  const alertSummary = ref<AlertSummary | null>(null)
  const pendingIncidents = ref<PendingIncident[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const escalateResult = ref<string | null>(null)

  async function fetchAlertSummary() {
    loading.value = true
    error.value = null
    try {
      alertSummary.value = await integrationApi.getAlertSummary()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load alert summary'
    } finally {
      loading.value = false
    }
  }

  async function fetchPendingIncidents() {
    loading.value = true
    error.value = null
    try {
      pendingIncidents.value = await integrationApi.getPendingIncidents()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load pending incidents'
    } finally {
      loading.value = false
    }
  }

  async function escalate(incidentId: string, requestedBy: string, changeReason: string) {
    error.value = null
    try {
      const result = await integrationApi.escalateToCAB(incidentId, requestedBy, changeReason)
      escalateResult.value = result.rfc_reference
      await fetchPendingIncidents()
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to escalate incident'
      return null
    }
  }

  return { alertSummary, pendingIncidents, loading, error, escalateResult, fetchAlertSummary, fetchPendingIncidents, escalate }
})
