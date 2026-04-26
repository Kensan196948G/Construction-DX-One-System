import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIncidentsStore } from '@/stores/incidents'
import { incidentsApi } from '@/api/incidents'
import type { Incident } from '@/types'

vi.mock('@/api/incidents', () => ({
  incidentsApi: {
    list: vi.fn(),
    create: vi.fn(),
    updateStatus: vi.fn(),
  },
}))

const mockIncident: Incident = {
  id: 'i1',
  incidentNumber: 'INC-0001',
  title: 'Test Incident',
  description: 'desc',
  severity: 'critical',
  status: 'open',
  affectedSystemsCount: 2,
  bcpActivated: false,
  declaredAt: '2024-01-01T00:00:00Z',
  resolvedAt: null,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
}

describe('useIncidentsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初期状態は空リスト', () => {
    const store = useIncidentsStore()
    expect(store.incidents).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchIncidents でインシデント一覧を取得する', async () => {
    vi.mocked(incidentsApi.list).mockResolvedValueOnce([mockIncident])
    const store = useIncidentsStore()
    await store.fetchIncidents()
    expect(incidentsApi.list).toHaveBeenCalledWith(undefined, undefined)
    expect(store.incidents).toHaveLength(1)
    expect(store.incidents[0].id).toBe('i1')
  })

  it('fetchIncidents にフィルター引数を渡す', async () => {
    vi.mocked(incidentsApi.list).mockResolvedValueOnce([])
    const store = useIncidentsStore()
    await store.fetchIncidents('open', 'critical')
    expect(incidentsApi.list).toHaveBeenCalledWith('open', 'critical')
  })

  it('fetchIncidents 中は loading が true', async () => {
    let resolve!: (v: Incident[]) => void
    vi.mocked(incidentsApi.list).mockReturnValueOnce(
      new Promise<Incident[]>((res) => { resolve = res })
    )
    const store = useIncidentsStore()
    const promise = store.fetchIncidents()
    expect(store.loading).toBe(true)
    resolve([])
    await promise
    expect(store.loading).toBe(false)
  })

  it('fetchIncidents 失敗時に error がセットされる', async () => {
    vi.mocked(incidentsApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useIncidentsStore()
    await store.fetchIncidents()
    expect(store.error).toBe('Network error')
    expect(store.incidents).toHaveLength(0)
  })

  it('createIncident で先頭に追加される', async () => {
    const existing = { ...mockIncident, id: 'i0', incidentNumber: 'INC-0000' }
    const newInc = { ...mockIncident, id: 'i1', incidentNumber: 'INC-0001' }
    vi.mocked(incidentsApi.create).mockResolvedValueOnce(newInc)
    const store = useIncidentsStore()
    store.incidents = [existing]
    await store.createIncident({ title: 'Test', severity: 'high' })
    expect(store.incidents[0].id).toBe('i1')
    expect(store.incidents).toHaveLength(2)
  })

  it('createIncident 失敗時は null を返す', async () => {
    vi.mocked(incidentsApi.create).mockRejectedValueOnce(new Error('fail'))
    const store = useIncidentsStore()
    const result = await store.createIncident({ title: 'T', severity: 'low' })
    expect(result).toBeNull()
    expect(store.error).toBe('fail')
  })

  it('updateIncidentStatus でリスト内を更新する', async () => {
    const updated = { ...mockIncident, status: 'investigating' as const }
    vi.mocked(incidentsApi.updateStatus).mockResolvedValueOnce(updated)
    const store = useIncidentsStore()
    store.incidents = [mockIncident]
    const ok = await store.updateIncidentStatus('i1', { status: 'investigating' })
    expect(ok).toBe(true)
    expect(store.incidents[0].status).toBe('investigating')
  })

  it('openIncidents は resolved/closed を除外する', () => {
    const store = useIncidentsStore()
    store.incidents = [
      mockIncident,
      { ...mockIncident, id: 'i2', status: 'resolved' },
      { ...mockIncident, id: 'i3', status: 'closed' },
      { ...mockIncident, id: 'i4', status: 'investigating' },
    ]
    expect(store.openIncidents()).toHaveLength(2)
  })

  it('criticalIncidents は severity=critical のみ返す', () => {
    const store = useIncidentsStore()
    store.incidents = [
      mockIncident,
      { ...mockIncident, id: 'i2', severity: 'high' },
      { ...mockIncident, id: 'i3', severity: 'critical' },
    ]
    expect(store.criticalIncidents()).toHaveLength(2)
  })

  it('bcpActivatedIncidents は bcpActivated=true のみ返す', () => {
    const store = useIncidentsStore()
    store.incidents = [
      mockIncident,
      { ...mockIncident, id: 'i2', bcpActivated: true },
      { ...mockIncident, id: 'i3', bcpActivated: true },
    ]
    expect(store.bcpActivatedIncidents()).toHaveLength(2)
  })
})
