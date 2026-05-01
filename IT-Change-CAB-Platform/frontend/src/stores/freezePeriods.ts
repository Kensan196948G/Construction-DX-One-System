import { defineStore } from 'pinia'
import { ref } from 'vue'
import { freezePeriodsApi } from '@/api/freezePeriods'
import type { FreezePeriod, FreezePeriodCreate } from '@/api/freezePeriods'

export const useFreezePeriodStore = defineStore('freezePeriods', () => {
  const freezePeriods = ref<FreezePeriod[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchFreezePeriods(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      freezePeriods.value = await freezePeriodsApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load freeze periods'
    } finally {
      loading.value = false
    }
  }

  async function createFreezePeriod(data: FreezePeriodCreate): Promise<FreezePeriod | null> {
    try {
      const created = await freezePeriodsApi.create(data)
      freezePeriods.value.unshift(created)
      return created
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create freeze period'
      return null
    }
  }

  async function deleteFreezePeriod(id: string): Promise<boolean> {
    try {
      await freezePeriodsApi.delete(id)
      const idx = freezePeriods.value.findIndex((fp) => fp.id === id)
      if (idx !== -1) freezePeriods.value.splice(idx, 1)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete freeze period'
      return false
    }
  }

  return {
    freezePeriods,
    loading,
    error,
    fetchFreezePeriods,
    createFreezePeriod,
    deleteFreezePeriod,
  }
})
