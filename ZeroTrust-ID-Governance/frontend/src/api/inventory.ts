import client from './client'

export type CampaignStatus = 'draft' | 'active' | 'completed' | 'cancelled'

export interface InventoryCampaign {
  id: string
  name: string
  description: string | null
  status: CampaignStatus
  review_period_start: string
  review_period_end: string
  total_accounts: number
  reviewed_count: number
  flagged_count: number
  created_by: string
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface InventoryCampaignCreate {
  name: string
  description?: string | null
  review_period_start: string
  review_period_end: string
}

export const inventoryApi = {
  listCampaigns(status?: CampaignStatus): Promise<InventoryCampaign[]> {
    return client
      .get<InventoryCampaign[]>('/inventory/campaigns', { params: status ? { status } : {} })
      .then((r) => r.data)
  },

  getCampaign(id: string): Promise<InventoryCampaign> {
    return client.get<InventoryCampaign>(`/inventory/campaigns/${id}`).then((r) => r.data)
  },

  createCampaign(data: InventoryCampaignCreate): Promise<InventoryCampaign> {
    return client.post<InventoryCampaign>('/inventory/campaigns', data).then((r) => r.data)
  },

  startCampaign(id: string): Promise<InventoryCampaign> {
    return client.post<InventoryCampaign>(`/inventory/campaigns/${id}/start`).then((r) => r.data)
  },

  completeCampaign(id: string): Promise<InventoryCampaign> {
    return client.post<InventoryCampaign>(`/inventory/campaigns/${id}/complete`).then((r) => r.data)
  },

  cancelCampaign(id: string): Promise<InventoryCampaign> {
    return client.post<InventoryCampaign>(`/inventory/campaigns/${id}/cancel`).then((r) => r.data)
  },
}
