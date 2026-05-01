import { defineStore } from 'pinia'
import { ref } from 'vue'
import { biaApi } from '@/api/bia'
import type { BiaCreateInput } from '@/api/bia'

export const useBiaStore = defineStore('bia', () => {
  const biaList = ref<any[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchBia() {
    loading.value = true
    error.value = null
    try {
      biaList.value = await biaApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load BIA records'
    } finally {
      loading.value = false
    }
  }

  async function createBia(data: BiaCreateInput): Promise<any | null> {
    try {
      const record = await biaApi.create(data)
      biaList.value.unshift(record)
      return record
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create BIA record'
      return null
    }
  }

  return {
    biaList,
    loading,
    error,
    fetchBia,
    createBia,
  }
})
