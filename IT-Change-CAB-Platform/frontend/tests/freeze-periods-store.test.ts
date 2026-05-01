import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useFreezePeriodStore } from '@/stores/freezePeriods'
import { freezePeriodsApi } from '@/api/freezePeriods'
import type { FreezePeriod } from '@/api/freezePeriods'

vi.mock('@/api/freezePeriods', () => ({
  freezePeriodsApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockFreezePeriod: FreezePeriod = {
  id: 'fp1',
  title: '年末年始凍結',
  start_date: '2026-12-28',
  end_date: '2027-01-04',
  reason: '年末年始のシステム安定運用のため',
  created_at: '2026-11-01T00:00:00Z',
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useFreezePeriodStore', () => {
  it('fetchFreezePeriods: 成功時に freezePeriods にデータがセットされる', async () => {
    vi.mocked(freezePeriodsApi.list).mockResolvedValueOnce([mockFreezePeriod])
    const store = useFreezePeriodStore()
    await store.fetchFreezePeriods()
    expect(store.freezePeriods).toHaveLength(1)
    expect(store.freezePeriods[0].title).toBe('年末年始凍結')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchFreezePeriods: 失敗時に error がセットされる', async () => {
    vi.mocked(freezePeriodsApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useFreezePeriodStore()
    await store.fetchFreezePeriods()
    expect(store.freezePeriods).toHaveLength(0)
    expect(store.error).toBe('Network error')
    expect(store.loading).toBe(false)
  })

  it('fetchFreezePeriods: ロード中は loading が true になる', async () => {
    let resolve!: (v: FreezePeriod[]) => void
    vi.mocked(freezePeriodsApi.list).mockReturnValueOnce(
      new Promise<FreezePeriod[]>((res) => { resolve = res }),
    )
    const store = useFreezePeriodStore()
    const fetchPromise = store.fetchFreezePeriods()
    expect(store.loading).toBe(true)
    resolve([mockFreezePeriod])
    await fetchPromise
    expect(store.loading).toBe(false)
  })

  it('createFreezePeriod: 成功時に先頭に追加される', async () => {
    const newFp: FreezePeriod = {
      id: 'fp2',
      title: 'GW凍結',
      start_date: '2027-04-29',
      end_date: '2027-05-05',
      reason: 'GW期間',
    }
    vi.mocked(freezePeriodsApi.create).mockResolvedValueOnce(newFp)
    const store = useFreezePeriodStore()
    store.freezePeriods = [mockFreezePeriod]
    const result = await store.createFreezePeriod({
      title: 'GW凍結',
      start_date: '2027-04-29',
      end_date: '2027-05-05',
      reason: 'GW期間',
    })
    expect(result).not.toBeNull()
    expect(store.freezePeriods).toHaveLength(2)
    expect(store.freezePeriods[0].id).toBe('fp2')
  })

  it('createFreezePeriod: 失敗時に null を返し error がセットされる', async () => {
    vi.mocked(freezePeriodsApi.create).mockRejectedValueOnce(new Error('Validation failed'))
    const store = useFreezePeriodStore()
    const result = await store.createFreezePeriod({
      title: '',
      start_date: '2027-01-01',
      end_date: '2027-01-05',
    })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation failed')
  })

  it('deleteFreezePeriod: 成功時にリストから削除される', async () => {
    vi.mocked(freezePeriodsApi.delete).mockResolvedValueOnce(undefined)
    const store = useFreezePeriodStore()
    store.freezePeriods = [mockFreezePeriod, { ...mockFreezePeriod, id: 'fp2', title: 'GW凍結' }]
    const ok = await store.deleteFreezePeriod('fp1')
    expect(ok).toBe(true)
    expect(store.freezePeriods).toHaveLength(1)
    expect(store.freezePeriods[0].id).toBe('fp2')
  })

  it('deleteFreezePeriod: 失敗時に false を返し error がセットされる', async () => {
    vi.mocked(freezePeriodsApi.delete).mockRejectedValueOnce(new Error('Forbidden'))
    const store = useFreezePeriodStore()
    store.freezePeriods = [mockFreezePeriod]
    const ok = await store.deleteFreezePeriod('fp1')
    expect(ok).toBe(false)
    expect(store.error).toBe('Forbidden')
    expect(store.freezePeriods).toHaveLength(1)
  })

  it('初期状態は空である', () => {
    const store = useFreezePeriodStore()
    expect(store.freezePeriods).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('createFreezePeriod: reason なしでも成功する', async () => {
    const newFp: FreezePeriod = { id: 'fp3', title: '緊急凍結', start_date: '2027-02-01', end_date: '2027-02-02' }
    vi.mocked(freezePeriodsApi.create).mockResolvedValueOnce(newFp)
    const store = useFreezePeriodStore()
    const result = await store.createFreezePeriod({
      title: '緊急凍結',
      start_date: '2027-02-01',
      end_date: '2027-02-02',
    })
    expect(result).not.toBeNull()
    expect(result?.reason).toBeUndefined()
  })
})
