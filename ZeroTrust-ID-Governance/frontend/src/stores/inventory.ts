import { defineStore } from 'pinia'
import { ref } from 'vue'
import { inventoryApi, type CampaignStatus, type InventoryCampaign, type InventoryCampaignCreate } from '@/api/inventory'

export const useInventoryStore = defineStore('inventory', () => {
  const campaigns = ref<InventoryCampaign[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchCampaigns(status?: CampaignStatus) {
    loading.value = true
    error.value = null
    try {
      campaigns.value = await inventoryApi.listCampaigns(status)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load campaigns'
    } finally {
      loading.value = false
    }
  }

  async function createCampaign(data: InventoryCampaignCreate): Promise<InventoryCampaign | null> {
    try {
      const campaign = await inventoryApi.createCampaign(data)
      campaigns.value.unshift(campaign)
      return campaign
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create campaign'
      return null
    }
  }

  async function startCampaign(id: string): Promise<boolean> {
    try {
      const updated = await inventoryApi.startCampaign(id)
      _replaceCampaign(updated)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start campaign'
      return false
    }
  }

  async function completeCampaign(id: string): Promise<boolean> {
    try {
      const updated = await inventoryApi.completeCampaign(id)
      _replaceCampaign(updated)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to complete campaign'
      return false
    }
  }

  async function cancelCampaign(id: string): Promise<boolean> {
    try {
      const updated = await inventoryApi.cancelCampaign(id)
      _replaceCampaign(updated)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to cancel campaign'
      return false
    }
  }

  function _replaceCampaign(updated: InventoryCampaign) {
    const idx = campaigns.value.findIndex((c) => c.id === updated.id)
    if (idx !== -1) campaigns.value.splice(idx, 1, updated)
  }

  const activeCampaigns = () => campaigns.value.filter((c) => c.status === 'active')
  const draftCampaigns = () => campaigns.value.filter((c) => c.status === 'draft')

  return {
    campaigns,
    loading,
    error,
    fetchCampaigns,
    createCampaign,
    startCampaign,
    completeCampaign,
    cancelCampaign,
    activeCampaigns,
    draftCampaigns,
  }
})
