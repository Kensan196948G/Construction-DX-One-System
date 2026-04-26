import { defineStore } from 'pinia'
import { ref } from 'vue'
import { incidentsApi } from '@/api/incidents'
import type { Incident, IncidentCreate, IncidentStatus, IncidentStatusUpdate, IncidentSeverity } from '@/types'

export const useIncidentsStore = defineStore('incidents', () => {
  const incidents = ref<Incident[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchIncidents(status?: IncidentStatus, severity?: IncidentSeverity) {
    loading.value = true
    error.value = null
    try {
      incidents.value = await incidentsApi.list(status, severity)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load incidents'
    } finally {
      loading.value = false
    }
  }

  async function createIncident(data: IncidentCreate): Promise<Incident | null> {
    try {
      const incident = await incidentsApi.create(data)
      incidents.value.unshift(incident)
      return incident
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create incident'
      return null
    }
  }

  async function updateIncidentStatus(id: string, data: IncidentStatusUpdate): Promise<boolean> {
    try {
      const updated = await incidentsApi.updateStatus(id, data)
      const idx = incidents.value.findIndex((i) => i.id === id)
      if (idx !== -1) incidents.value.splice(idx, 1, updated)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update incident status'
      return false
    }
  }

  const openIncidents = () => incidents.value.filter((i) =>
    i.status !== 'resolved' && i.status !== 'closed'
  )
  const criticalIncidents = () => incidents.value.filter((i) => i.severity === 'critical')
  const bcpActivatedIncidents = () => incidents.value.filter((i) => i.bcpActivated)

  return {
    incidents,
    loading,
    error,
    fetchIncidents,
    createIncident,
    updateIncidentStatus,
    openIncidents,
    criticalIncidents,
    bcpActivatedIncidents,
  }
})
