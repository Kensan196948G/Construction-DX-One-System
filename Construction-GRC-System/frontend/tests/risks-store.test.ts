import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRisksStore } from '@/stores/risks'
import { risksApi } from '@/api/risks'

vi.mock('@/api/risks', () => ({
  risksApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockRisk = {
  id: 'abc-123',
  title: 'Test Risk',
  description: '',
  category: 'Security',
  likelihood: 4,
  impact: 5,
  risk_score: 20,
  status: 'open' as const,
  owner: 'Alice',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('useRisksStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchRisks sets risks on success', async () => {
    vi.mocked(risksApi.list).mockResolvedValueOnce([mockRisk])
    const store = useRisksStore()
    await store.fetchRisks()
    expect(store.risks).toHaveLength(1)
    expect(store.risks[0].title).toBe('Test Risk')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchRisks sets error on failure', async () => {
    vi.mocked(risksApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useRisksStore()
    await store.fetchRisks()
    expect(store.risks).toHaveLength(0)
    expect(store.error).toBe('Network error')
  })

  it('createRisk prepends to list', async () => {
    vi.mocked(risksApi.create).mockResolvedValueOnce(mockRisk)
    const store = useRisksStore()
    const result = await store.createRisk({ title: 'Test Risk', likelihood: 4, impact: 5 })
    expect(result).toEqual(mockRisk)
    expect(store.risks[0]).toEqual(mockRisk)
  })

  it('createRisk returns null on failure', async () => {
    vi.mocked(risksApi.create).mockRejectedValueOnce(new Error('Bad request'))
    const store = useRisksStore()
    const result = await store.createRisk({ title: '', likelihood: 1, impact: 1 })
    expect(result).toBeNull()
    expect(store.error).toBe('Bad request')
  })

  it('updateRisk replaces the risk in list', async () => {
    const updated = { ...mockRisk, title: 'Updated Risk' }
    vi.mocked(risksApi.update).mockResolvedValueOnce(updated)
    const store = useRisksStore()
    store.risks = [mockRisk]
    const result = await store.updateRisk('abc-123', { title: 'Updated Risk', likelihood: 4, impact: 5 })
    expect(result).toBe(true)
    expect(store.risks[0].title).toBe('Updated Risk')
  })

  it('deleteRisk removes the risk from list', async () => {
    vi.mocked(risksApi.delete).mockResolvedValueOnce(undefined)
    const store = useRisksStore()
    store.risks = [mockRisk]
    const result = await store.deleteRisk('abc-123')
    expect(result).toBe(true)
    expect(store.risks).toHaveLength(0)
  })

  it('openRisks returns only open risks', () => {
    const store = useRisksStore()
    store.risks = [
      mockRisk,
      { ...mockRisk, id: 'xyz', status: 'closed' as const },
    ]
    expect(store.openRisks()).toHaveLength(1)
  })

  it('highRisks returns risks with score >= 15', () => {
    const store = useRisksStore()
    store.risks = [
      mockRisk,
      { ...mockRisk, id: 'low', risk_score: 10 },
    ]
    expect(store.highRisks()).toHaveLength(1)
  })
})
