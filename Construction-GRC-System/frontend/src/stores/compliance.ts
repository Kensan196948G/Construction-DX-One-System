import { defineStore } from 'pinia'
import { ref } from 'vue'
import { complianceApi } from '@/api/compliance'
import type { Control, ControlCreate } from '@/types'

export interface SoAEntry {
  control_number: string
  title: string
  applicability: Control['applicability']
  implementation_status: Control['implementation_status']
  justification: string
}

export const useComplianceStore = defineStore('compliance', () => {
  const controls = ref<Control[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const soa = ref<SoAEntry[]>([])

  async function fetchControls(implementation_status?: string, applicability?: string) {
    loading.value = true
    error.value = null
    try {
      controls.value = await complianceApi.list(implementation_status, applicability)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load controls'
    } finally {
      loading.value = false
    }
  }

  async function createControl(data: ControlCreate): Promise<Control | null> {
    try {
      const control = await complianceApi.create(data)
      controls.value.unshift(control)
      return control
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create control'
      return null
    }
  }

  async function updateControl(id: string, data: ControlCreate): Promise<boolean> {
    try {
      const updated = await complianceApi.update(id, data)
      const idx = controls.value.findIndex((c) => c.id === id)
      if (idx !== -1) controls.value[idx] = updated
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update control'
      return false
    }
  }

  async function assessControl(
    id: string,
    data: Partial<Pick<ControlCreate, 'implementation_status' | 'justification'>>,
  ): Promise<boolean> {
    const control = controls.value.find((c) => c.id === id)
    if (!control) return false
    return updateControl(id, { ...control, ...data })
  }

  async function fetchSoA() {
    try {
      const all = await complianceApi.list()
      soa.value = all.map((c) => ({
        control_number: c.control_number,
        title: c.title,
        applicability: c.applicability,
        implementation_status: c.implementation_status,
        justification: c.justification,
      }))
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load SoA'
    }
  }

  return {
    controls,
    loading,
    error,
    soa,
    fetchControls,
    createControl,
    updateControl,
    assessControl,
    fetchSoA,
  }
})
