import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useInventoryStore } from '@/stores/inventory'
import { inventoryApi } from '@/api/inventory'

vi.mock('@/api/inventory', () => ({
  inventoryApi: {
    listCampaigns: vi.fn(),
    getCampaign: vi.fn(),
    createCampaign: vi.fn(),
    startCampaign: vi.fn(),
    completeCampaign: vi.fn(),
    cancelCampaign: vi.fn(),
  },
}))

const mockCampaign = {
  id: 'c1',
  name: '2026年Q1 棚卸',
  description: 'Q1定期棚卸',
  status: 'draft' as const,
  review_period_start: '2026-01-01',
  review_period_end: '2026-03-31',
  total_accounts: 100,
  reviewed_count: 0,
  flagged_count: 0,
  created_by: 'admin-user-id',
  completed_at: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('useInventoryStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchCampaigns sets campaigns on success', async () => {
    vi.mocked(inventoryApi.listCampaigns).mockResolvedValueOnce([mockCampaign])
    const store = useInventoryStore()
    await store.fetchCampaigns()
    expect(store.campaigns).toHaveLength(1)
    expect(store.campaigns[0].name).toBe('2026年Q1 棚卸')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchCampaigns sets error on failure', async () => {
    vi.mocked(inventoryApi.listCampaigns).mockRejectedValueOnce(new Error('Network error'))
    const store = useInventoryStore()
    await store.fetchCampaigns()
    expect(store.campaigns).toHaveLength(0)
    expect(store.error).toBe('Network error')
    expect(store.loading).toBe(false)
  })

  it('fetchCampaigns passes status filter', async () => {
    vi.mocked(inventoryApi.listCampaigns).mockResolvedValueOnce([mockCampaign])
    const store = useInventoryStore()
    await store.fetchCampaigns('draft')
    expect(inventoryApi.listCampaigns).toHaveBeenCalledWith('draft')
  })

  it('createCampaign prepends to campaigns list', async () => {
    vi.mocked(inventoryApi.createCampaign).mockResolvedValueOnce(mockCampaign)
    const store = useInventoryStore()
    const result = await store.createCampaign({
      name: '2026年Q1 棚卸',
      review_period_start: '2026-01-01',
      review_period_end: '2026-03-31',
    })
    expect(result).toEqual(mockCampaign)
    expect(store.campaigns[0]).toEqual(mockCampaign)
  })

  it('createCampaign returns null on failure', async () => {
    vi.mocked(inventoryApi.createCampaign).mockRejectedValueOnce(new Error('Validation error'))
    const store = useInventoryStore()
    const result = await store.createCampaign({
      name: '',
      review_period_start: '',
      review_period_end: '',
    })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation error')
  })

  it('startCampaign updates campaign status to active', async () => {
    const activeCampaign = { ...mockCampaign, status: 'active' as const }
    vi.mocked(inventoryApi.startCampaign).mockResolvedValueOnce(activeCampaign)
    const store = useInventoryStore()
    store.campaigns = [mockCampaign]
    const result = await store.startCampaign('c1')
    expect(result).toBe(true)
    expect(store.campaigns[0].status).toBe('active')
  })

  it('startCampaign returns false on failure', async () => {
    vi.mocked(inventoryApi.startCampaign).mockRejectedValueOnce(new Error('Already started'))
    const store = useInventoryStore()
    const result = await store.startCampaign('c1')
    expect(result).toBe(false)
    expect(store.error).toBe('Already started')
  })

  it('completeCampaign updates campaign status to completed', async () => {
    const activeCampaign = { ...mockCampaign, status: 'active' as const }
    const completedCampaign = { ...mockCampaign, status: 'completed' as const }
    vi.mocked(inventoryApi.completeCampaign).mockResolvedValueOnce(completedCampaign)
    const store = useInventoryStore()
    store.campaigns = [activeCampaign]
    const result = await store.completeCampaign('c1')
    expect(result).toBe(true)
    expect(store.campaigns[0].status).toBe('completed')
  })

  it('cancelCampaign updates campaign status to cancelled', async () => {
    const cancelledCampaign = { ...mockCampaign, status: 'cancelled' as const }
    vi.mocked(inventoryApi.cancelCampaign).mockResolvedValueOnce(cancelledCampaign)
    const store = useInventoryStore()
    store.campaigns = [mockCampaign]
    const result = await store.cancelCampaign('c1')
    expect(result).toBe(true)
    expect(store.campaigns[0].status).toBe('cancelled')
  })

  it('cancelCampaign returns false on failure', async () => {
    vi.mocked(inventoryApi.cancelCampaign).mockRejectedValueOnce(new Error('Already cancelled'))
    const store = useInventoryStore()
    const result = await store.cancelCampaign('c1')
    expect(result).toBe(false)
    expect(store.error).toBe('Already cancelled')
  })

  it('activeCampaigns returns only active campaigns', () => {
    const store = useInventoryStore()
    store.campaigns = [
      mockCampaign,
      { ...mockCampaign, id: 'c2', status: 'active' as const },
      { ...mockCampaign, id: 'c3', status: 'completed' as const },
    ]
    expect(store.activeCampaigns()).toHaveLength(1)
    expect(store.activeCampaigns()[0].id).toBe('c2')
  })

  it('draftCampaigns returns only draft campaigns', () => {
    const store = useInventoryStore()
    store.campaigns = [
      mockCampaign,
      { ...mockCampaign, id: 'c2', status: 'active' as const },
      { ...mockCampaign, id: 'c3', status: 'draft' as const },
    ]
    expect(store.draftCampaigns()).toHaveLength(2)
  })
})
