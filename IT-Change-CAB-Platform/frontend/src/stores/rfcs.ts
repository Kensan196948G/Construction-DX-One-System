import { defineStore } from 'pinia'
import { ref } from 'vue'
import { rfcsApi } from '@/api/rfcs'
import type { Rfc, RfcCreate, RfcStatus, RfcStatusUpdate, ChangeType, ChangePriority } from '@/types'

export const useRfcsStore = defineStore('rfcs', () => {
  const rfcs = ref<Rfc[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchRfcs(status?: RfcStatus, changeType?: ChangeType, priority?: ChangePriority) {
    loading.value = true
    error.value = null
    try {
      rfcs.value = await rfcsApi.list(status, changeType, priority)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load RFCs'
    } finally {
      loading.value = false
    }
  }

  async function createRfc(data: RfcCreate): Promise<Rfc | null> {
    try {
      const rfc = await rfcsApi.create(data)
      rfcs.value.unshift(rfc)
      return rfc
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create RFC'
      return null
    }
  }

  async function updateRfcStatus(id: string, data: RfcStatusUpdate): Promise<boolean> {
    try {
      const updated = await rfcsApi.updateStatus(id, data)
      const idx = rfcs.value.findIndex((r) => r.id === id)
      if (idx !== -1) rfcs.value.splice(idx, 1, updated)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update RFC status'
      return false
    }
  }

  const pendingRfcs = () => rfcs.value.filter((r) => r.status === 'pending_approval' || r.status === 'cab_review')
  const inProgressRfcs = () => rfcs.value.filter((r) => r.status === 'in_progress')
  const highRiskRfcs = () => rfcs.value.filter((r) => r.technicalRisk === 'high')

  return {
    rfcs,
    loading,
    error,
    fetchRfcs,
    createRfc,
    updateRfcStatus,
    pendingRfcs,
    inProgressRfcs,
    highRiskRfcs,
  }
})
