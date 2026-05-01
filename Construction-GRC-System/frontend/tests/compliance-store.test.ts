import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useComplianceStore } from '@/stores/compliance'
import { complianceApi } from '@/api/compliance'

vi.mock('@/api/compliance', () => ({
  complianceApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockControl = {
  id: 'ctrl-1',
  control_number: 'A.5.1',
  title: 'Information Security Policies',
  domain: 'Policies',
  applicability: 'applicable' as const,
  implementation_status: 'not_started' as const,
  description: 'Policy management',
  justification: '',
  created_at: '2026-05-01T00:00:00Z',
  updated_at: '2026-05-01T00:00:00Z',
}

describe('useComplianceStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchControls sets controls on success', async () => {
    vi.mocked(complianceApi.list).mockResolvedValueOnce([mockControl])
    const store = useComplianceStore()
    await store.fetchControls()
    expect(store.controls).toHaveLength(1)
    expect(store.controls[0].control_number).toBe('A.5.1')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchControls sets error on failure', async () => {
    vi.mocked(complianceApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useComplianceStore()
    await store.fetchControls()
    expect(store.controls).toHaveLength(0)
    expect(store.error).toBe('Network error')
  })

  it('createControl prepends to list', async () => {
    vi.mocked(complianceApi.create).mockResolvedValueOnce(mockControl)
    const store = useComplianceStore()
    const result = await store.createControl({
      control_number: 'A.5.1',
      title: 'Information Security Policies',
      domain: 'Policies',
    })
    expect(result).toEqual(mockControl)
    expect(store.controls[0]).toEqual(mockControl)
  })

  it('createControl returns null on failure', async () => {
    vi.mocked(complianceApi.create).mockRejectedValueOnce(new Error('Validation error'))
    const store = useComplianceStore()
    const result = await store.createControl({ control_number: '', title: '', domain: '' })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation error')
  })

  it('updateControl replaces control in list', async () => {
    const updated = { ...mockControl, implementation_status: 'in_progress' as const }
    vi.mocked(complianceApi.update).mockResolvedValueOnce(updated)
    const store = useComplianceStore()
    store.controls = [mockControl]
    const result = await store.updateControl('ctrl-1', {
      ...mockControl,
      implementation_status: 'in_progress',
    })
    expect(result).toBe(true)
    expect(store.controls[0].implementation_status).toBe('in_progress')
  })

  it('updateControl returns false on failure', async () => {
    vi.mocked(complianceApi.update).mockRejectedValueOnce(new Error('Server error'))
    const store = useComplianceStore()
    const result = await store.updateControl('ctrl-1', { ...mockControl })
    expect(result).toBe(false)
    expect(store.error).toBe('Server error')
  })

  it('assessControl updates implementation_status via updateControl', async () => {
    const updated = { ...mockControl, implementation_status: 'implemented' as const }
    vi.mocked(complianceApi.update).mockResolvedValueOnce(updated)
    const store = useComplianceStore()
    store.controls = [mockControl]
    const result = await store.assessControl('ctrl-1', { implementation_status: 'implemented' })
    expect(result).toBe(true)
    expect(store.controls[0].implementation_status).toBe('implemented')
  })

  it('assessControl returns false when control not found', async () => {
    const store = useComplianceStore()
    store.controls = []
    const result = await store.assessControl('nonexistent', { implementation_status: 'verified' })
    expect(result).toBe(false)
  })

  it('fetchSoA builds SoA from controls list', async () => {
    vi.mocked(complianceApi.list).mockResolvedValueOnce([mockControl])
    const store = useComplianceStore()
    await store.fetchSoA()
    expect(store.soa).toHaveLength(1)
    expect(store.soa[0].control_number).toBe('A.5.1')
    expect(store.soa[0].applicability).toBe('applicable')
    expect(store.soa[0].implementation_status).toBe('not_started')
  })

  it('fetchSoA sets error on failure', async () => {
    vi.mocked(complianceApi.list).mockRejectedValueOnce(new Error('SoA error'))
    const store = useComplianceStore()
    await store.fetchSoA()
    expect(store.error).toBe('SoA error')
    expect(store.soa).toHaveLength(0)
  })
})
