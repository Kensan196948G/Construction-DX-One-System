import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useEventsStore } from '@/stores/events'
import { eventsApi } from '@/api/events'

vi.mock('@/api/events', () => ({
  eventsApi: {
    list: vi.fn(),
    get: vi.fn(),
    ingest: vi.fn(),
    bulkIngest: vi.fn(),
    markProcessed: vi.fn(),
  },
}))

const mockEvent = {
  id: 'e1',
  event_type: 'authentication_failure',
  severity: 'high' as const,
  source_ip: '192.168.1.100',
  source_hostname: 'host-a',
  destination_ip: '10.0.0.1',
  destination_port: 22,
  occurred_at: '2026-05-01T00:00:00Z',
  ingested_at: '2026-05-01T00:00:01Z',
  raw_log: null,
  log_source: 'syslog',
  risk_score: 75,
  correlation_id: null,
  is_processed: false,
}

describe('useEventsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchEvents sets events on success', async () => {
    vi.mocked(eventsApi.list).mockResolvedValueOnce([mockEvent])
    const store = useEventsStore()
    await store.fetchEvents()
    expect(store.events).toHaveLength(1)
    expect(store.events[0].event_type).toBe('authentication_failure')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchEvents sets error on failure', async () => {
    vi.mocked(eventsApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useEventsStore()
    await store.fetchEvents()
    expect(store.events).toHaveLength(0)
    expect(store.error).toBe('Network error')
  })

  it('fetchEvents passes limit and offset to api', async () => {
    vi.mocked(eventsApi.list).mockResolvedValueOnce([mockEvent])
    const store = useEventsStore()
    await store.fetchEvents(10, 20)
    expect(eventsApi.list).toHaveBeenCalledWith(undefined, 10, 20)
  })

  it('createEvent prepends to list', async () => {
    vi.mocked(eventsApi.ingest).mockResolvedValueOnce(mockEvent)
    const store = useEventsStore()
    const result = await store.createEvent({ event_type: 'authentication_failure' })
    expect(result).toEqual(mockEvent)
    expect(store.events[0]).toEqual(mockEvent)
  })

  it('createEvent returns null on failure', async () => {
    vi.mocked(eventsApi.ingest).mockRejectedValueOnce(new Error('Validation error'))
    const store = useEventsStore()
    const result = await store.createEvent({ event_type: '' })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation error')
  })

  it('fetchStats computes stats from events list', async () => {
    const processedEvent = { ...mockEvent, id: 'e2', severity: 'medium' as const, is_processed: true }
    vi.mocked(eventsApi.list).mockResolvedValueOnce([mockEvent, processedEvent])
    const store = useEventsStore()
    await store.fetchStats()
    expect(store.stats).not.toBeNull()
    expect(store.stats!.total).toBe(2)
    expect(store.stats!.processed).toBe(1)
    expect(store.stats!.unprocessed).toBe(1)
    expect(store.stats!.by_severity['high']).toBe(1)
    expect(store.stats!.by_severity['medium']).toBe(1)
  })

  it('fetchStats sets error on failure', async () => {
    vi.mocked(eventsApi.list).mockRejectedValueOnce(new Error('Stats error'))
    const store = useEventsStore()
    await store.fetchStats()
    expect(store.error).toBe('Stats error')
    expect(store.stats).toBeNull()
  })

  it('loading is false after fetchEvents completes', async () => {
    vi.mocked(eventsApi.list).mockResolvedValueOnce([])
    const store = useEventsStore()
    const promise = store.fetchEvents()
    expect(store.loading).toBe(true)
    await promise
    expect(store.loading).toBe(false)
  })
})
