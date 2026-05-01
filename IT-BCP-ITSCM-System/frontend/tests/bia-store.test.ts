import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useBiaStore } from '@/stores/bia'
import { biaApi } from '@/api/bia'
import type { BiaRecord, ImpactLevel } from '@/types'

vi.mock('@/api/bia', () => ({
  biaApi: {
    list: vi.fn(),
    create: vi.fn(),
  },
}))

const mockBiaRecord: BiaRecord = {
  id: 'bia-1',
  system_id: 'sys-001',
  assessment_date: '2024-01-15',
  rto_hours: 4,
  rpo_hours: 1,
  impact_level: 'critical',
  notes: 'Core ERP system assessment',
}

describe('useBiaStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初期状態は空リスト', () => {
    const store = useBiaStore()
    expect(store.biaList).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchBia で BIA レコード一覧を取得する', async () => {
    vi.mocked(biaApi.list).mockResolvedValueOnce([mockBiaRecord])
    const store = useBiaStore()
    await store.fetchBia()
    expect(biaApi.list).toHaveBeenCalledOnce()
    expect(store.biaList).toHaveLength(1)
    expect(store.biaList[0].id).toBe('bia-1')
  })

  it('fetchBia 中は loading が true になる', async () => {
    let resolve!: (v: any[]) => void
    vi.mocked(biaApi.list).mockReturnValueOnce(
      new Promise<any[]>((res) => {
        resolve = res
      }),
    )
    const store = useBiaStore()
    const promise = store.fetchBia()
    expect(store.loading).toBe(true)
    resolve([])
    await promise
    expect(store.loading).toBe(false)
  })

  it('fetchBia 失敗時に error がセットされ biaList は空のまま', async () => {
    vi.mocked(biaApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useBiaStore()
    await store.fetchBia()
    expect(store.error).toBe('Network error')
    expect(store.biaList).toHaveLength(0)
  })

  it('fetchBia 失敗時に Error 以外のオブジェクトでもデフォルトメッセージを返す', async () => {
    vi.mocked(biaApi.list).mockRejectedValueOnce('unknown error')
    const store = useBiaStore()
    await store.fetchBia()
    expect(store.error).toBe('Failed to load BIA records')
  })

  it('createBia で biaList の先頭に追加される', async () => {
    const existing = { ...mockBiaRecord, id: 'bia-0' }
    const newRecord = { ...mockBiaRecord, id: 'bia-1' }
    vi.mocked(biaApi.create).mockResolvedValueOnce(newRecord)
    const store = useBiaStore()
    store.biaList = [existing]
    const result = await store.createBia({
      system_id: 'sys-001',
      assessment_date: '2024-01-15',
      rto_hours: 4,
      rpo_hours: 1,
      impact_level: 'critical' as ImpactLevel,
    })
    expect(result).toEqual(newRecord)
    expect(store.biaList[0].id).toBe('bia-1')
    expect(store.biaList).toHaveLength(2)
  })

  it('createBia 失敗時は null を返し error がセットされる', async () => {
    vi.mocked(biaApi.create).mockRejectedValueOnce(new Error('Create failed'))
    const store = useBiaStore()
    const result = await store.createBia({
      system_id: 'sys-002',
      assessment_date: '2024-02-01',
      rto_hours: 8,
      rpo_hours: 2,
      impact_level: 'high' as ImpactLevel,
    })
    expect(result).toBeNull()
    expect(store.error).toBe('Create failed')
  })

  it('createBia 後に fetchBia を実行すると error がリセットされる', async () => {
    vi.mocked(biaApi.create).mockRejectedValueOnce(new Error('fail'))
    vi.mocked(biaApi.list).mockResolvedValueOnce([mockBiaRecord])
    const store = useBiaStore()
    await store.createBia({
      system_id: 'sys-003',
      assessment_date: '2024-03-01',
      rto_hours: 2,
      rpo_hours: 0.5,
      impact_level: 'medium' as ImpactLevel,
    })
    expect(store.error).toBe('fail')
    await store.fetchBia()
    expect(store.error).toBeNull()
    expect(store.biaList).toHaveLength(1)
  })

  it('createBia 成功時は notes を含めて API に渡す', async () => {
    vi.mocked(biaApi.create).mockResolvedValueOnce({ ...mockBiaRecord, notes: 'test note' })
    const store = useBiaStore()
    const input = {
      system_id: 'sys-004',
      assessment_date: '2024-04-01',
      rto_hours: 4,
      rpo_hours: 1,
      impact_level: 'low' as ImpactLevel,
      notes: 'test note',
    }
    await store.createBia(input)
    expect(biaApi.create).toHaveBeenCalledWith(input)
  })
})
