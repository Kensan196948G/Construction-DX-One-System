import { defineStore } from 'pinia'
import { ref } from 'vue'
import { alertsApi } from '@/api/alerts'
import type { Alert, AlertCreate, AlertStatus, AlertSeverity } from '@/types'

export const useAlertsStore = defineStore('alerts', () => {
  const alerts = ref<Alert[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAlerts(status?: AlertStatus, severity?: AlertSeverity) {
    loading.value = true
    error.value = null
    try {
      alerts.value = await alertsApi.list(status, severity)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load alerts'
    } finally {
      loading.value = false
    }
  }

  async function createAlert(data: AlertCreate): Promise<Alert | null> {
    try {
      const alert = await alertsApi.create(data)
      alerts.value.unshift(alert)
      return alert
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create alert'
      return null
    }
  }

  async function updateAlertStatus(id: string, status: AlertStatus): Promise<boolean> {
    try {
      const updated = await alertsApi.updateStatus(id, { status })
      const idx = alerts.value.findIndex((a) => a.id === id)
      if (idx !== -1) alerts.value.splice(idx, 1, updated)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update alert status'
      return false
    }
  }

  const openAlerts = () => alerts.value.filter((a) => a.status === 'open')
  const criticalAlerts = () =>
    alerts.value.filter((a) => a.severity === 'critical' || a.severity === 'high')

  return {
    alerts,
    loading,
    error,
    fetchAlerts,
    createAlert,
    updateAlertStatus,
    openAlerts,
    criticalAlerts,
  }
})
