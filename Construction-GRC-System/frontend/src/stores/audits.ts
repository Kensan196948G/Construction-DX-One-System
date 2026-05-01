import { defineStore } from 'pinia'
import { ref } from 'vue'
import { auditsApi } from '@/api/audits'
import type { Audit, AuditCreate } from '@/types'

export const useAuditsStore = defineStore('audits', () => {
  const audits = ref<Audit[]>([])
  const currentAudit = ref<Audit | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAudits(status?: string) {
    loading.value = true
    error.value = null
    try {
      audits.value = await auditsApi.list(status)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load audits'
    } finally {
      loading.value = false
    }
  }

  async function fetchAudit(id: string) {
    loading.value = true
    error.value = null
    try {
      currentAudit.value = await auditsApi.get(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load audit'
    } finally {
      loading.value = false
    }
  }

  async function createAudit(data: AuditCreate): Promise<Audit | null> {
    try {
      const audit = await auditsApi.create(data)
      audits.value.unshift(audit)
      return audit
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create audit'
      return null
    }
  }

  async function updateAudit(id: string, data: AuditCreate): Promise<boolean> {
    try {
      const updated = await auditsApi.update(id, data)
      const idx = audits.value.findIndex((a) => a.id === id)
      if (idx !== -1) audits.value[idx] = updated
      if (currentAudit.value?.id === id) currentAudit.value = updated
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update audit'
      return false
    }
  }

  return {
    audits,
    currentAudit,
    loading,
    error,
    fetchAudits,
    fetchAudit,
    createAudit,
    updateAudit,
  }
})
