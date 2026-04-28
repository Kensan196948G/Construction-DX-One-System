import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIntegrationStore } from '@/stores/integration'
import { integrationApi } from '@/api/integration'
import type { IdentitySummary, AuthEvent, AuthEventsResponse } from '@/api/integration'

vi.mock('@/api/integration', () => ({
  integrationApi: {
    getIdentitySummary: vi.fn(),
    getRecentAuthEvents: vi.fn(),
    sendWebhookNotify: vi.fn(),
  },
}))

const mockIdentitySummary: IdentitySummary = {
  total_users: 150,
  active_users: 130,
  privileged_users: 8,
  generated_at: '2026-04-28T10:00:00Z',
}

const mockAuthEvent: AuthEvent = {
  id: 'evt-001',
  event_type: 'login_success',
  username: 'tanaka',
  actor_ip: '192.168.1.10',
  severity: 'low',
  timestamp: '2026-04-28T09:55:00Z',
}

const mockFailedEvent: AuthEvent = {
  id: 'evt-002',
  event_type: 'login_failure',
  username: 'yamada',
  actor_ip: '10.0.0.5',
  severity: 'high',
  timestamp: '2026-04-28T09:58:00Z',
}

const mockAuthEventsResponse: AuthEventsResponse = {
  events: [mockAuthEvent, mockFailedEvent],
  total_count: 2,
  period_hours: 1,
}

describe('useIntegrationStore (ZTIG)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initial state is empty', () => {
    const store = useIntegrationStore()
    expect(store.identitySummary).toBeNull()
    expect(store.authEvents).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.periodHours).toBe(1)
  })

  it('fetchIdentitySummary sets identitySummary on success', async () => {
    vi.mocked(integrationApi.getIdentitySummary).mockResolvedValueOnce(mockIdentitySummary)
    const store = useIntegrationStore()
    await store.fetchIdentitySummary()

    expect(store.identitySummary).toEqual(mockIdentitySummary)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchIdentitySummary sets error on failure', async () => {
    vi.mocked(integrationApi.getIdentitySummary).mockRejectedValueOnce(new Error('ZTIG backend down'))
    const store = useIntegrationStore()
    await store.fetchIdentitySummary()

    expect(store.identitySummary).toBeNull()
    expect(store.error).toBe('ZTIG backend down')
    expect(store.loading).toBe(false)
  })

  it('fetchIdentitySummary sets fallback error for non-Error rejection', async () => {
    vi.mocked(integrationApi.getIdentitySummary).mockRejectedValueOnce('server failure')
    const store = useIntegrationStore()
    await store.fetchIdentitySummary()

    expect(store.error).toBe('Failed to load identity summary')
  })

  it('fetchAuthEvents sets authEvents with default 1 hour', async () => {
    vi.mocked(integrationApi.getRecentAuthEvents).mockResolvedValueOnce(mockAuthEventsResponse)
    const store = useIntegrationStore()
    await store.fetchAuthEvents()

    expect(store.authEvents).toEqual(mockAuthEventsResponse)
    expect(store.periodHours).toBe(1)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(integrationApi.getRecentAuthEvents).toHaveBeenCalledWith(1)
  })

  it('fetchAuthEvents updates periodHours to given value', async () => {
    const response6h: AuthEventsResponse = { ...mockAuthEventsResponse, period_hours: 6 }
    vi.mocked(integrationApi.getRecentAuthEvents).mockResolvedValueOnce(response6h)
    const store = useIntegrationStore()
    await store.fetchAuthEvents(6)

    expect(store.periodHours).toBe(6)
    expect(store.authEvents?.period_hours).toBe(6)
    expect(integrationApi.getRecentAuthEvents).toHaveBeenCalledWith(6)
  })

  it('fetchAuthEvents handles 24 hour period', async () => {
    const response24h: AuthEventsResponse = {
      events: [],
      total_count: 0,
      period_hours: 24,
    }
    vi.mocked(integrationApi.getRecentAuthEvents).mockResolvedValueOnce(response24h)
    const store = useIntegrationStore()
    await store.fetchAuthEvents(24)

    expect(store.periodHours).toBe(24)
    expect(store.authEvents?.events).toHaveLength(0)
    expect(store.authEvents?.total_count).toBe(0)
  })

  it('fetchAuthEvents sets error on failure', async () => {
    vi.mocked(integrationApi.getRecentAuthEvents).mockRejectedValueOnce(new Error('Timeout'))
    const store = useIntegrationStore()
    await store.fetchAuthEvents(1)

    expect(store.authEvents).toBeNull()
    expect(store.error).toBe('Timeout')
    expect(store.loading).toBe(false)
  })

  it('fetchAuthEvents sets fallback error for non-Error rejection', async () => {
    vi.mocked(integrationApi.getRecentAuthEvents).mockRejectedValueOnce(null)
    const store = useIntegrationStore()
    await store.fetchAuthEvents(1)

    expect(store.error).toBe('Failed to load auth events')
  })

  it('clears previous error on new fetchIdentitySummary call', async () => {
    vi.mocked(integrationApi.getIdentitySummary).mockRejectedValueOnce(new Error('first error'))
    const store = useIntegrationStore()
    await store.fetchIdentitySummary()
    expect(store.error).toBe('first error')

    vi.mocked(integrationApi.getIdentitySummary).mockResolvedValueOnce(mockIdentitySummary)
    await store.fetchIdentitySummary()
    expect(store.error).toBeNull()
  })

  it('clears previous error on new fetchAuthEvents call', async () => {
    vi.mocked(integrationApi.getRecentAuthEvents).mockRejectedValueOnce(new Error('network error'))
    const store = useIntegrationStore()
    await store.fetchAuthEvents(1)
    expect(store.error).toBe('network error')

    vi.mocked(integrationApi.getRecentAuthEvents).mockResolvedValueOnce(mockAuthEventsResponse)
    await store.fetchAuthEvents(1)
    expect(store.error).toBeNull()
  })

  it('identitySummary reflects correct counts', async () => {
    vi.mocked(integrationApi.getIdentitySummary).mockResolvedValueOnce(mockIdentitySummary)
    const store = useIntegrationStore()
    await store.fetchIdentitySummary()

    expect(store.identitySummary?.total_users).toBe(150)
    expect(store.identitySummary?.active_users).toBe(130)
    expect(store.identitySummary?.privileged_users).toBe(8)
  })

  it('authEvents contains correct event data', async () => {
    vi.mocked(integrationApi.getRecentAuthEvents).mockResolvedValueOnce(mockAuthEventsResponse)
    const store = useIntegrationStore()
    await store.fetchAuthEvents(1)

    expect(store.authEvents?.events[0].event_type).toBe('login_success')
    expect(store.authEvents?.events[1].severity).toBe('high')
    expect(store.authEvents?.total_count).toBe(2)
  })
})
