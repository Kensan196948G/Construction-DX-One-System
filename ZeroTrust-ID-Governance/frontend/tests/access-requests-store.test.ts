import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAccessRequestsStore } from '@/stores/accessRequests'
import { accessRequestsApi } from '@/api/accessRequests'

vi.mock('@/api/accessRequests', () => ({
  accessRequestsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    cancel: vi.fn(),
  },
}))

const mockRequest = {
  id: 'r1',
  requester_id: 'u1',
  requester_name: '田中 太郎',
  requested_role: 'read_only',
  resource: '/reports/financial',
  reason: '月次レポート確認のため',
  status: 'pending' as const,
  created_at: '2026-04-25T09:00:00Z',
  reviewed_at: null,
  reviewed_by: null,
  expires_at: null,
}

describe('useAccessRequestsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchRequests sets requests on success', async () => {
    vi.mocked(accessRequestsApi.list).mockResolvedValueOnce([mockRequest])
    const store = useAccessRequestsStore()
    await store.fetchRequests()
    expect(store.requests).toHaveLength(1)
    expect(store.requests[0].requester_name).toBe('田中 太郎')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchRequests sets error on failure', async () => {
    vi.mocked(accessRequestsApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useAccessRequestsStore()
    await store.fetchRequests()
    expect(store.requests).toHaveLength(0)
    expect(store.error).toBe('Network error')
    expect(store.loading).toBe(false)
  })

  it('fetchRequests passes status filter', async () => {
    vi.mocked(accessRequestsApi.list).mockResolvedValueOnce([mockRequest])
    const store = useAccessRequestsStore()
    await store.fetchRequests('pending')
    expect(accessRequestsApi.list).toHaveBeenCalledWith('pending')
  })

  it('createRequest prepends to requests list', async () => {
    vi.mocked(accessRequestsApi.create).mockResolvedValueOnce(mockRequest)
    const store = useAccessRequestsStore()
    const result = await store.createRequest({ requested_role: 'read_only', reason: 'テスト' })
    expect(result).toEqual(mockRequest)
    expect(store.requests[0]).toEqual(mockRequest)
  })

  it('createRequest returns null on failure', async () => {
    vi.mocked(accessRequestsApi.create).mockRejectedValueOnce(new Error('Forbidden'))
    const store = useAccessRequestsStore()
    const result = await store.createRequest({ requested_role: '', reason: '' })
    expect(result).toBeNull()
    expect(store.error).toBe('Forbidden')
  })

  it('approveRequest replaces request in list', async () => {
    const approved = { ...mockRequest, status: 'approved' as const, reviewed_at: '2026-04-25T10:00:00Z', reviewed_by: 'admin' }
    vi.mocked(accessRequestsApi.approve).mockResolvedValueOnce(approved)
    const store = useAccessRequestsStore()
    store.requests = [mockRequest]
    const result = await store.approveRequest('r1')
    expect(result).toBe(true)
    expect(store.requests[0].status).toBe('approved')
  })

  it('approveRequest returns false on failure', async () => {
    vi.mocked(accessRequestsApi.approve).mockRejectedValueOnce(new Error('Not found'))
    const store = useAccessRequestsStore()
    const result = await store.approveRequest('nonexistent')
    expect(result).toBe(false)
    expect(store.error).toBe('Not found')
  })

  it('rejectRequest replaces request in list', async () => {
    const rejected = { ...mockRequest, status: 'rejected' as const }
    vi.mocked(accessRequestsApi.reject).mockResolvedValueOnce(rejected)
    const store = useAccessRequestsStore()
    store.requests = [mockRequest]
    const result = await store.rejectRequest('r1')
    expect(result).toBe(true)
    expect(store.requests[0].status).toBe('rejected')
  })

  it('rejectRequest returns false on failure', async () => {
    vi.mocked(accessRequestsApi.reject).mockRejectedValueOnce(new Error('Forbidden'))
    const store = useAccessRequestsStore()
    const result = await store.rejectRequest('nonexistent')
    expect(result).toBe(false)
  })

  it('pendingRequests returns only pending requests', () => {
    const store = useAccessRequestsStore()
    store.requests = [
      mockRequest,
      { ...mockRequest, id: 'r2', status: 'approved' as const },
      { ...mockRequest, id: 'r3', status: 'rejected' as const },
    ]
    expect(store.pendingRequests()).toHaveLength(1)
    expect(store.pendingRequests()[0].id).toBe('r1')
  })

  it('approvedRequests returns only approved requests', () => {
    const store = useAccessRequestsStore()
    store.requests = [
      mockRequest,
      { ...mockRequest, id: 'r2', status: 'approved' as const },
    ]
    expect(store.approvedRequests()).toHaveLength(1)
    expect(store.approvedRequests()[0].id).toBe('r2')
  })
})
