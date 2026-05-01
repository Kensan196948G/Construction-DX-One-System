import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuditsStore } from '@/stores/audits'
import { auditsApi } from '@/api/audits'

vi.mock('@/api/audits', () => ({
  auditsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    listFindings: vi.fn(),
    createFinding: vi.fn(),
  },
}))

const mockAudit = {
  id: 'aud-1',
  title: 'Annual Security Audit',
  scope: 'Full system',
  auditor: 'Alice',
  status: 'planned' as const,
  planned_date: '2026-06-01',
  completed_date: null,
  findings: [],
  findings_count: 0,
  created_at: '2026-05-01T00:00:00Z',
  updated_at: '2026-05-01T00:00:00Z',
}

describe('useAuditsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchAudits sets audits on success', async () => {
    vi.mocked(auditsApi.list).mockResolvedValueOnce([mockAudit])
    const store = useAuditsStore()
    await store.fetchAudits()
    expect(store.audits).toHaveLength(1)
    expect(store.audits[0].title).toBe('Annual Security Audit')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchAudits sets error on failure', async () => {
    vi.mocked(auditsApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useAuditsStore()
    await store.fetchAudits()
    expect(store.audits).toHaveLength(0)
    expect(store.error).toBe('Network error')
  })

  it('fetchAudit sets currentAudit on success', async () => {
    vi.mocked(auditsApi.get).mockResolvedValueOnce(mockAudit)
    const store = useAuditsStore()
    await store.fetchAudit('aud-1')
    expect(store.currentAudit).toEqual(mockAudit)
    expect(store.loading).toBe(false)
  })

  it('fetchAudit sets error on failure', async () => {
    vi.mocked(auditsApi.get).mockRejectedValueOnce(new Error('Not found'))
    const store = useAuditsStore()
    await store.fetchAudit('nonexistent')
    expect(store.currentAudit).toBeNull()
    expect(store.error).toBe('Not found')
  })

  it('createAudit prepends to list', async () => {
    vi.mocked(auditsApi.create).mockResolvedValueOnce(mockAudit)
    const store = useAuditsStore()
    const result = await store.createAudit({ title: 'Annual Security Audit' })
    expect(result).toEqual(mockAudit)
    expect(store.audits[0]).toEqual(mockAudit)
  })

  it('createAudit returns null on failure', async () => {
    vi.mocked(auditsApi.create).mockRejectedValueOnce(new Error('Validation error'))
    const store = useAuditsStore()
    const result = await store.createAudit({ title: '' })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation error')
  })

  it('updateAudit replaces audit in list', async () => {
    const updated = { ...mockAudit, status: 'in_progress' as const }
    vi.mocked(auditsApi.update).mockResolvedValueOnce(updated)
    const store = useAuditsStore()
    store.audits = [mockAudit]
    const result = await store.updateAudit('aud-1', { title: 'Annual Security Audit', status: 'in_progress' })
    expect(result).toBe(true)
    expect(store.audits[0].status).toBe('in_progress')
  })

  it('updateAudit also updates currentAudit if matching', async () => {
    const updated = { ...mockAudit, status: 'completed' as const }
    vi.mocked(auditsApi.update).mockResolvedValueOnce(updated)
    const store = useAuditsStore()
    store.audits = [mockAudit]
    store.currentAudit = mockAudit
    await store.updateAudit('aud-1', { title: 'Annual Security Audit', status: 'completed' })
    expect(store.currentAudit!.status).toBe('completed')
  })

  it('updateAudit returns false on failure', async () => {
    vi.mocked(auditsApi.update).mockRejectedValueOnce(new Error('Server error'))
    const store = useAuditsStore()
    const result = await store.updateAudit('aud-1', { title: 'Annual Security Audit' })
    expect(result).toBe(false)
    expect(store.error).toBe('Server error')
  })
})
