import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRfcsStore } from '@/stores/rfcs'
import { rfcsApi } from '@/api/rfcs'
import type { Rfc } from '@/types'

vi.mock('@/api/rfcs', () => ({
  rfcsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    updateStatus: vi.fn(),
  },
}))

const mockRfc: Rfc = {
  id: 'r1',
  rfcNumber: 'RFC-0001',
  title: 'Test Change',
  description: null,
  changeType: 'normal',
  priority: 'medium',
  status: 'pending_approval',
  targetSystems: ['WebServer'],
  affectedUsers: 100,
  plannedStart: '2026-05-01T09:00:00Z',
  plannedEnd: '2026-05-01T17:00:00Z',
  businessImpact: null,
  technicalRisk: 'low',
  riskScore: 8,
  rollbackPlan: null,
  requester: { id: 'u1', displayName: 'Alice' },
  createdAt: '2026-04-01T00:00:00Z',
  updatedAt: '2026-04-01T00:00:00Z',
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useRfcsStore', () => {
  it('fetchRfcs sets rfcs on success', async () => {
    vi.mocked(rfcsApi.list).mockResolvedValueOnce([mockRfc])
    const store = useRfcsStore()
    await store.fetchRfcs()
    expect(store.rfcs).toHaveLength(1)
    expect(store.rfcs[0].rfcNumber).toBe('RFC-0001')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchRfcs passes filter params', async () => {
    vi.mocked(rfcsApi.list).mockResolvedValueOnce([])
    const store = useRfcsStore()
    await store.fetchRfcs('pending_approval', 'normal', 'high')
    expect(rfcsApi.list).toHaveBeenCalledWith('pending_approval', 'normal', 'high')
  })

  it('fetchRfcs sets error on failure', async () => {
    vi.mocked(rfcsApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useRfcsStore()
    await store.fetchRfcs()
    expect(store.rfcs).toHaveLength(0)
    expect(store.error).toBe('Network error')
  })

  it('createRfc prepends to list on success', async () => {
    const newRfc: Rfc = { ...mockRfc, id: 'r2', rfcNumber: 'RFC-0002', title: 'New Change' }
    vi.mocked(rfcsApi.create).mockResolvedValueOnce(newRfc)
    const store = useRfcsStore()
    store.rfcs = [mockRfc]
    const result = await store.createRfc({
      title: 'New Change',
      changeType: 'normal',
      priority: 'medium',
      targetSystems: ['DB'],
      plannedStart: '2026-06-01T09:00:00Z',
      plannedEnd: '2026-06-01T17:00:00Z',
      technicalRisk: 'low',
    })
    expect(result).not.toBeNull()
    expect(store.rfcs[0].rfcNumber).toBe('RFC-0002')
    expect(store.rfcs).toHaveLength(2)
  })

  it('createRfc returns null on failure', async () => {
    vi.mocked(rfcsApi.create).mockRejectedValueOnce(new Error('Validation failed'))
    const store = useRfcsStore()
    const result = await store.createRfc({
      title: 'Bad RFC',
      changeType: 'normal',
      priority: 'low',
      targetSystems: [],
      plannedStart: '2026-06-01T09:00:00Z',
      plannedEnd: '2026-06-01T17:00:00Z',
      technicalRisk: 'low',
    })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation failed')
  })

  it('updateRfcStatus replaces rfc in list', async () => {
    const updated: Rfc = { ...mockRfc, status: 'approved' }
    vi.mocked(rfcsApi.updateStatus).mockResolvedValueOnce(updated)
    const store = useRfcsStore()
    store.rfcs = [mockRfc]
    const ok = await store.updateRfcStatus('r1', { status: 'approved' })
    expect(ok).toBe(true)
    expect(store.rfcs[0].status).toBe('approved')
  })

  it('updateRfcStatus returns false on failure', async () => {
    vi.mocked(rfcsApi.updateStatus).mockRejectedValueOnce(new Error('Forbidden'))
    const store = useRfcsStore()
    store.rfcs = [mockRfc]
    const ok = await store.updateRfcStatus('r1', { status: 'cancelled' })
    expect(ok).toBe(false)
    expect(store.error).toBe('Forbidden')
  })

  it('pendingRfcs returns pending_approval and cab_review', () => {
    const store = useRfcsStore()
    store.rfcs = [
      mockRfc,
      { ...mockRfc, id: 'r2', status: 'cab_review' },
      { ...mockRfc, id: 'r3', status: 'approved' },
      { ...mockRfc, id: 'r4', status: 'draft' },
    ]
    expect(store.pendingRfcs()).toHaveLength(2)
  })

  it('inProgressRfcs returns only in_progress', () => {
    const store = useRfcsStore()
    store.rfcs = [
      mockRfc,
      { ...mockRfc, id: 'r2', status: 'in_progress' },
      { ...mockRfc, id: 'r3', status: 'in_progress' },
    ]
    expect(store.inProgressRfcs()).toHaveLength(2)
  })

  it('highRiskRfcs returns only high technical risk', () => {
    const store = useRfcsStore()
    store.rfcs = [
      mockRfc,
      { ...mockRfc, id: 'r2', technicalRisk: 'high' },
      { ...mockRfc, id: 'r3', technicalRisk: 'medium' },
      { ...mockRfc, id: 'r4', technicalRisk: 'high' },
    ]
    expect(store.highRiskRfcs()).toHaveLength(2)
  })

  it('initial state is empty', () => {
    const store = useRfcsStore()
    expect(store.rfcs).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })
})
