import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useKpiStore } from '@/stores/kpi'
import { kpiApi } from '@/api/kpi'
import type { KpiDashboard } from '@/api/kpi'

vi.mock('@/api/kpi', () => ({
  kpiApi: {
    getDashboard: vi.fn(),
  },
}))

const mockKpiData: KpiDashboard = {
  change_success_rate: 0.92,
  total_changes: 120,
  successful_changes: 110,
  failed_changes: 10,
  avg_lead_time_days: 3.5,
  pending_approvals: 5,
  open_rfcs: 8,
  emergency_changes: 2,
  cab_meetings_this_month: 3,
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useKpiStore', () => {
  it('fetchKpi: 成功時に kpiData にデータがセットされる', async () => {
    vi.mocked(kpiApi.getDashboard).mockResolvedValueOnce(mockKpiData)
    const store = useKpiStore()
    await store.fetchKpi()
    expect(store.kpiData).not.toBeNull()
    expect(store.kpiData?.change_success_rate).toBe(0.92)
    expect(store.kpiData?.total_changes).toBe(120)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchKpi: 失敗時に error がセットされ kpiData は null のまま', async () => {
    vi.mocked(kpiApi.getDashboard).mockRejectedValueOnce(new Error('Server error'))
    const store = useKpiStore()
    await store.fetchKpi()
    expect(store.kpiData).toBeNull()
    expect(store.error).toBe('Server error')
    expect(store.loading).toBe(false)
  })

  it('fetchKpi: ロード中は loading が true になる', async () => {
    let resolve!: (v: KpiDashboard) => void
    vi.mocked(kpiApi.getDashboard).mockReturnValueOnce(
      new Promise<KpiDashboard>((res) => { resolve = res }),
    )
    const store = useKpiStore()
    const fetchPromise = store.fetchKpi()
    expect(store.loading).toBe(true)
    resolve(mockKpiData)
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('fetchKpi: 複数回呼び出しても error がリセットされる', async () => {
    vi.mocked(kpiApi.getDashboard).mockRejectedValueOnce(new Error('First error'))
    const store = useKpiStore()
    await store.fetchKpi()
    expect(store.error).toBe('First error')

    vi.mocked(kpiApi.getDashboard).mockResolvedValueOnce(mockKpiData)
    await store.fetchKpi()
    expect(store.error).toBeNull()
    expect(store.kpiData?.change_success_rate).toBe(0.92)
  })

  it('初期状態: kpiData は null、loading は false、error は null', () => {
    const store = useKpiStore()
    expect(store.kpiData).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchKpi: 部分的なデータでも正しくセットされる', async () => {
    const partialData: KpiDashboard = {
      change_success_rate: null,
      total_changes: 50,
    }
    vi.mocked(kpiApi.getDashboard).mockResolvedValueOnce(partialData)
    const store = useKpiStore()
    await store.fetchKpi()
    expect(store.kpiData?.total_changes).toBe(50)
    expect(store.kpiData?.change_success_rate).toBeNull()
  })

  it('fetchKpi: getDashboard が正確に1回呼ばれる', async () => {
    vi.mocked(kpiApi.getDashboard).mockResolvedValueOnce(mockKpiData)
    const store = useKpiStore()
    await store.fetchKpi()
    expect(kpiApi.getDashboard).toHaveBeenCalledTimes(1)
  })
})
