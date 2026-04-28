import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useIntegrationStore } from '@/stores/integration'
import { integrationApi } from '@/api/integration'
import type { AlertSummary, PendingIncident, EscalateResult } from '@/api/integration'

vi.mock('@/api/integration', () => ({
  integrationApi: {
    getAlertSummary: vi.fn(),
    getPendingIncidents: vi.fn(),
    escalateToCAB: vi.fn(),
  },
}))

const mockAlertSummary: AlertSummary = {
  total_open: 12,
  critical_count: 2,
  high_count: 4,
  medium_count: 5,
  low_count: 1,
  generated_at: '2026-04-28T10:00:00Z',
}

const mockIncident: PendingIncident = {
  id: 'inc-001',
  title: 'Brute Force Attack Detected',
  severity: 'high',
  status: 'open',
  detected_at: '2026-04-28T09:00:00Z',
}

const mockIncident2: PendingIncident = {
  id: 'inc-002',
  title: 'Ransomware Activity',
  severity: 'critical',
  status: 'open',
  detected_at: '2026-04-28T09:30:00Z',
}

const mockEscalateResult: EscalateResult = {
  escalated: true,
  rfc_reference: 'RFC-2026-0042',
  incident_id: 'inc-001',
}

describe('useIntegrationStore (SIEM)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initial state is empty', () => {
    const store = useIntegrationStore()
    expect(store.alertSummary).toBeNull()
    expect(store.pendingIncidents).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.escalateResult).toBeNull()
  })

  it('fetchAlertSummary sets alertSummary on success', async () => {
    vi.mocked(integrationApi.getAlertSummary).mockResolvedValueOnce(mockAlertSummary)
    const store = useIntegrationStore()
    await store.fetchAlertSummary()

    expect(store.alertSummary).toEqual(mockAlertSummary)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchAlertSummary sets error on failure', async () => {
    vi.mocked(integrationApi.getAlertSummary).mockRejectedValueOnce(new Error('API unreachable'))
    const store = useIntegrationStore()
    await store.fetchAlertSummary()

    expect(store.alertSummary).toBeNull()
    expect(store.error).toBe('API unreachable')
    expect(store.loading).toBe(false)
  })

  it('fetchAlertSummary sets fallback error message for non-Error rejection', async () => {
    vi.mocked(integrationApi.getAlertSummary).mockRejectedValueOnce('unknown error')
    const store = useIntegrationStore()
    await store.fetchAlertSummary()

    expect(store.error).toBe('Failed to load alert summary')
  })

  it('fetchPendingIncidents sets incidents on success', async () => {
    vi.mocked(integrationApi.getPendingIncidents).mockResolvedValueOnce([mockIncident, mockIncident2])
    const store = useIntegrationStore()
    await store.fetchPendingIncidents()

    expect(store.pendingIncidents).toHaveLength(2)
    expect(store.pendingIncidents[0].id).toBe('inc-001')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchPendingIncidents sets empty array on empty response', async () => {
    vi.mocked(integrationApi.getPendingIncidents).mockResolvedValueOnce([])
    const store = useIntegrationStore()
    await store.fetchPendingIncidents()

    expect(store.pendingIncidents).toHaveLength(0)
    expect(store.error).toBeNull()
  })

  it('fetchPendingIncidents sets error on failure', async () => {
    vi.mocked(integrationApi.getPendingIncidents).mockRejectedValueOnce(new Error('Network error'))
    const store = useIntegrationStore()
    await store.fetchPendingIncidents()

    expect(store.pendingIncidents).toHaveLength(0)
    expect(store.error).toBe('Network error')
  })

  it('escalate sets escalateResult to rfc_reference on success', async () => {
    vi.mocked(integrationApi.escalateToCAB).mockResolvedValueOnce(mockEscalateResult)
    vi.mocked(integrationApi.getPendingIncidents).mockResolvedValueOnce([mockIncident2])
    const store = useIntegrationStore()
    const result = await store.escalate('inc-001', 'SIEM-Admin', 'High-severity incident')

    expect(result).toEqual(mockEscalateResult)
    expect(store.escalateResult).toBe('RFC-2026-0042')
    expect(store.error).toBeNull()
  })

  it('escalate calls escalateToCAB with correct arguments', async () => {
    vi.mocked(integrationApi.escalateToCAB).mockResolvedValueOnce(mockEscalateResult)
    vi.mocked(integrationApi.getPendingIncidents).mockResolvedValueOnce([])
    const store = useIntegrationStore()
    await store.escalate('inc-001', 'SIEM-Admin', 'Ransomware activity detected')

    expect(integrationApi.escalateToCAB).toHaveBeenCalledWith(
      'inc-001',
      'SIEM-Admin',
      'Ransomware activity detected',
    )
  })

  it('escalate refreshes pending incidents after success', async () => {
    vi.mocked(integrationApi.escalateToCAB).mockResolvedValueOnce(mockEscalateResult)
    vi.mocked(integrationApi.getPendingIncidents).mockResolvedValueOnce([mockIncident2])
    const store = useIntegrationStore()
    store.pendingIncidents = [mockIncident, mockIncident2]

    await store.escalate('inc-001', 'SIEM-Admin', 'High-severity incident')

    expect(integrationApi.getPendingIncidents).toHaveBeenCalledOnce()
    expect(store.pendingIncidents).toHaveLength(1)
    expect(store.pendingIncidents[0].id).toBe('inc-002')
  })

  it('escalate returns null and sets error on failure', async () => {
    vi.mocked(integrationApi.escalateToCAB).mockRejectedValueOnce(new Error('CAB unavailable'))
    const store = useIntegrationStore()
    const result = await store.escalate('inc-001', 'SIEM-Admin', 'reason')

    expect(result).toBeNull()
    expect(store.error).toBe('CAB unavailable')
    expect(store.escalateResult).toBeNull()
  })

  it('escalate sets fallback error for non-Error rejection', async () => {
    vi.mocked(integrationApi.escalateToCAB).mockRejectedValueOnce('server error')
    const store = useIntegrationStore()
    await store.escalate('inc-001', 'SIEM-Admin', 'reason')

    expect(store.error).toBe('Failed to escalate incident')
  })

  it('clears previous error before each fetch', async () => {
    vi.mocked(integrationApi.getAlertSummary).mockRejectedValueOnce(new Error('first error'))
    const store = useIntegrationStore()
    await store.fetchAlertSummary()
    expect(store.error).toBe('first error')

    vi.mocked(integrationApi.getAlertSummary).mockResolvedValueOnce(mockAlertSummary)
    await store.fetchAlertSummary()
    expect(store.error).toBeNull()
  })
})
