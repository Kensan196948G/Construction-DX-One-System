import { defineStore } from 'pinia'
import { ref } from 'vue'
import { accessRequestsApi } from '@/api/accessRequests'
import type { AccessRequest, AccessRequestCreate } from '@/types'

export const useAccessRequestsStore = defineStore('accessRequests', () => {
  const requests = ref<AccessRequest[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchRequests(status?: string) {
    loading.value = true
    error.value = null
    try {
      requests.value = await accessRequestsApi.list(status)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load requests'
    } finally {
      loading.value = false
    }
  }

  async function createRequest(data: AccessRequestCreate): Promise<AccessRequest | null> {
    try {
      const req = await accessRequestsApi.create(data)
      requests.value.unshift(req)
      return req
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create request'
      return null
    }
  }

  async function approveRequest(id: string): Promise<boolean> {
    try {
      const updated = await accessRequestsApi.approve(id)
      const idx = requests.value.findIndex((r) => r.id === id)
      if (idx !== -1) requests.value.splice(idx, 1, updated)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to approve request'
      return false
    }
  }

  async function rejectRequest(id: string): Promise<boolean> {
    try {
      const updated = await accessRequestsApi.reject(id)
      const idx = requests.value.findIndex((r) => r.id === id)
      if (idx !== -1) requests.value.splice(idx, 1, updated)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to reject request'
      return false
    }
  }

  const pendingRequests = () => requests.value.filter((r) => r.status === 'pending')
  const approvedRequests = () => requests.value.filter((r) => r.status === 'approved')

  return {
    requests,
    loading,
    error,
    fetchRequests,
    createRequest,
    approveRequest,
    rejectRequest,
    pendingRequests,
    approvedRequests,
  }
})
