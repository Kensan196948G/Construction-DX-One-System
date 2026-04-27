import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useSystemsStore } from '@/stores/systems'
import { systemsApi } from '@/api/systems'
import type { ItSystem } from '@/types'

vi.mock('@/api/systems', () => ({
  systemsApi: {
    list: vi.fn(),
  },
}))

const mockSystem: ItSystem = {
  id: 's1',
  systemName: 'Core ERP',
  description: 'Core system',
  tier: 'tier1',
  status: 'normal',
  rtoMinutes: 60,
  rpoMinutes: 30,
  recoveryPriority: 1,
  owner: 'IT Dept',
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

describe('useSystemsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初期状態は空リスト', () => {
    const store = useSystemsStore()
    expect(store.systems).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchSystems でシステム一覧を取得する', async () => {
    vi.mocked(systemsApi.list).mockResolvedValueOnce([mockSystem])
    const store = useSystemsStore()
    await store.fetchSystems()
    expect(systemsApi.list).toHaveBeenCalledWith(undefined, undefined)
    expect(store.systems).toHaveLength(1)
    expect(store.systems[0].id).toBe('s1')
  })

  it('fetchSystems にフィルター引数を渡す', async () => {
    vi.mocked(systemsApi.list).mockResolvedValueOnce([])
    const store = useSystemsStore()
    await store.fetchSystems('tier1', 'normal')
    expect(systemsApi.list).toHaveBeenCalledWith('tier1', 'normal')
  })

  it('fetchSystems 中は loading が true', async () => {
    let resolve!: (v: ItSystem[]) => void
    vi.mocked(systemsApi.list).mockReturnValueOnce(
      new Promise<ItSystem[]>((res) => { resolve = res })
    )
    const store = useSystemsStore()
    const promise = store.fetchSystems()
    expect(store.loading).toBe(true)
    resolve([])
    await promise
    expect(store.loading).toBe(false)
  })

  it('fetchSystems 失敗時に error がセットされる', async () => {
    vi.mocked(systemsApi.list).mockRejectedValueOnce(new Error('API error'))
    const store = useSystemsStore()
    await store.fetchSystems()
    expect(store.error).toBe('API error')
  })

  it('tier1Systems は tier1 のみ返す', () => {
    const store = useSystemsStore()
    store.systems = [
      mockSystem,
      { ...mockSystem, id: 's2', tier: 'tier2' },
      { ...mockSystem, id: 's3', tier: 'tier1' },
    ]
    expect(store.tier1Systems()).toHaveLength(2)
  })

  it('degradedSystems は degraded と down を返す', () => {
    const store = useSystemsStore()
    store.systems = [
      mockSystem,
      { ...mockSystem, id: 's2', status: 'degraded' },
      { ...mockSystem, id: 's3', status: 'down' },
      { ...mockSystem, id: 's4', status: 'maintenance' },
    ]
    expect(store.degradedSystems()).toHaveLength(2)
    expect(store.degradedSystems().map((s) => s.id)).toEqual(['s2', 's3'])
  })
})
