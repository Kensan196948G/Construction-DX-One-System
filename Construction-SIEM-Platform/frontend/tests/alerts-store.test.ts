import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAlertsStore } from '@/stores/alerts'
import { alertsApi } from '@/api/alerts'

vi.mock('@/api/alerts', () => ({
  alertsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    updateStatus: vi.fn(),
  },
}))

const mockAlert = {
  id: 'a1',
  title: 'Brute Force',
  description: null,
  severity: 'high' as const,
  status: 'open' as const,
  risk_score: 80,
  event_count: 50,
  rule_name: 'brute-force-rule',
  correlation_id: null,
  assigned_to: null,
  mitre_technique: 'T1110',
  mitre_tactic: 'credential-access',
  detected_at: '2026-04-25T00:00:00Z',
  resolved_at: null,
}

describe('useAlertsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchAlerts sets alerts on success', async () => {
    vi.mocked(alertsApi.list).mockResolvedValueOnce([mockAlert])
    const store = useAlertsStore()
    await store.fetchAlerts()
    expect(store.alerts).toHaveLength(1)
    expect(store.alerts[0].title).toBe('Brute Force')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchAlerts sets error on failure', async () => {
    vi.mocked(alertsApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useAlertsStore()
    await store.fetchAlerts()
    expect(store.alerts).toHaveLength(0)
    expect(store.error).toBe('Network error')
  })

  it('fetchAlerts passes status and severity filters', async () => {
    vi.mocked(alertsApi.list).mockResolvedValueOnce([mockAlert])
    const store = useAlertsStore()
    await store.fetchAlerts('open', 'high')
    expect(alertsApi.list).toHaveBeenCalledWith('open', 'high')
  })

  it('createAlert prepends to list', async () => {
    vi.mocked(alertsApi.create).mockResolvedValueOnce(mockAlert)
    const store = useAlertsStore()
    const result = await store.createAlert({ title: 'Brute Force', severity: 'high' })
    expect(result).toEqual(mockAlert)
    expect(store.alerts[0]).toEqual(mockAlert)
  })

  it('createAlert returns null on failure', async () => {
    vi.mocked(alertsApi.create).mockRejectedValueOnce(new Error('Validation error'))
    const store = useAlertsStore()
    const result = await store.createAlert({ title: '' })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation error')
  })

  it('updateAlertStatus replaces alert in list', async () => {
    const updated = { ...mockAlert, status: 'resolved' as const }
    vi.mocked(alertsApi.updateStatus).mockResolvedValueOnce(updated)
    const store = useAlertsStore()
    store.alerts = [mockAlert]
    const result = await store.updateAlertStatus('a1', 'resolved')
    expect(result).toBe(true)
    expect(store.alerts[0].status).toBe('resolved')
  })

  it('updateAlertStatus returns false on failure', async () => {
    vi.mocked(alertsApi.updateStatus).mockRejectedValueOnce(new Error('Not found'))
    const store = useAlertsStore()
    const result = await store.updateAlertStatus('nonexistent', 'resolved')
    expect(result).toBe(false)
  })

  it('openAlerts returns only open alerts', () => {
    const store = useAlertsStore()
    store.alerts = [
      mockAlert,
      { ...mockAlert, id: 'a2', status: 'resolved' as const },
    ]
    expect(store.openAlerts()).toHaveLength(1)
    expect(store.openAlerts()[0].id).toBe('a1')
  })

  it('criticalAlerts returns high and critical alerts', () => {
    const store = useAlertsStore()
    store.alerts = [
      mockAlert,
      { ...mockAlert, id: 'a2', severity: 'medium' as const },
    ]
    expect(store.criticalAlerts()).toHaveLength(1)
    expect(store.criticalAlerts()[0].severity).toBe('high')
  })
})
