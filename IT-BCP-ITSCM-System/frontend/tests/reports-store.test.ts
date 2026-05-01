import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useReportsStore } from '@/stores/reports'
import { reportsApi } from '@/api/reports'

vi.mock('@/api/reports', () => ({
  reportsApi: {
    getExecutiveSummary: vi.fn(),
    getSystemStatus: vi.fn(),
  },
}))

const mockExecutiveSummary = {
  total_incidents: 42,
  critical_incidents: 5,
  critical_rate: 0.119,
  bcp_activations: 2,
  avg_recovery_hours: 3.7,
  open_incidents: 8,
}

const mockSystemStatus = {
  total_systems: 20,
  normal_systems: 16,
  degraded_systems: 3,
  down_systems: 1,
  tier1_count: 5,
  availability_rate: 0.95,
}

describe('useReportsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初期状態は null', () => {
    const store = useReportsStore()
    expect(store.executiveSummary).toBeNull()
    expect(store.systemStatus).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchExecutiveSummary でサマリーを取得する', async () => {
    vi.mocked(reportsApi.getExecutiveSummary).mockResolvedValueOnce(mockExecutiveSummary)
    const store = useReportsStore()
    await store.fetchExecutiveSummary()
    expect(reportsApi.getExecutiveSummary).toHaveBeenCalledOnce()
    expect(store.executiveSummary).toEqual(mockExecutiveSummary)
    expect(store.error).toBeNull()
  })

  it('fetchExecutiveSummary 失敗時に error がセットされ executiveSummary は null のまま', async () => {
    vi.mocked(reportsApi.getExecutiveSummary).mockRejectedValueOnce(new Error('API error'))
    const store = useReportsStore()
    await store.fetchExecutiveSummary()
    expect(store.error).toBe('API error')
    expect(store.executiveSummary).toBeNull()
  })

  it('fetchSystemStatus でシステム状態を取得する', async () => {
    vi.mocked(reportsApi.getSystemStatus).mockResolvedValueOnce(mockSystemStatus)
    const store = useReportsStore()
    await store.fetchSystemStatus()
    expect(reportsApi.getSystemStatus).toHaveBeenCalledOnce()
    expect(store.systemStatus).toEqual(mockSystemStatus)
    expect(store.error).toBeNull()
  })

  it('fetchSystemStatus 失敗時に error がセットされ systemStatus は null のまま', async () => {
    vi.mocked(reportsApi.getSystemStatus).mockRejectedValueOnce(new Error('Timeout'))
    const store = useReportsStore()
    await store.fetchSystemStatus()
    expect(store.error).toBe('Timeout')
    expect(store.systemStatus).toBeNull()
  })

  it('fetchExecutiveSummary 中は loading が true になる', async () => {
    let resolve!: (v: any) => void
    vi.mocked(reportsApi.getExecutiveSummary).mockReturnValueOnce(
      new Promise<any>((res) => {
        resolve = res
      }),
    )
    const store = useReportsStore()
    const promise = store.fetchExecutiveSummary()
    expect(store.loading).toBe(true)
    resolve(mockExecutiveSummary)
    await promise
    expect(store.loading).toBe(false)
  })

  it('fetchSystemStatus 中は loading が true になる', async () => {
    let resolve!: (v: any) => void
    vi.mocked(reportsApi.getSystemStatus).mockReturnValueOnce(
      new Promise<any>((res) => {
        resolve = res
      }),
    )
    const store = useReportsStore()
    const promise = store.fetchSystemStatus()
    expect(store.loading).toBe(true)
    resolve(mockSystemStatus)
    await promise
    expect(store.loading).toBe(false)
  })

  it('fetchExecutiveSummary 失敗後に再度成功すると error がクリアされる', async () => {
    vi.mocked(reportsApi.getExecutiveSummary)
      .mockRejectedValueOnce(new Error('first fail'))
      .mockResolvedValueOnce(mockExecutiveSummary)
    const store = useReportsStore()
    await store.fetchExecutiveSummary()
    expect(store.error).toBe('first fail')
    await store.fetchExecutiveSummary()
    expect(store.error).toBeNull()
    expect(store.executiveSummary).toEqual(mockExecutiveSummary)
  })

  it('Error 以外のオブジェクト throw 時にデフォルトメッセージを返す', async () => {
    vi.mocked(reportsApi.getSystemStatus).mockRejectedValueOnce('unexpected string error')
    const store = useReportsStore()
    await store.fetchSystemStatus()
    expect(store.error).toBe('Failed to load system status')
  })
})
