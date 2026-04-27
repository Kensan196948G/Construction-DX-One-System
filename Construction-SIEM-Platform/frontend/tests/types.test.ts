import { describe, it, expect } from 'vitest'
import { severityWeight } from '@/types'
import type { SecurityEvent, Alert, AlertStatus, EventSeverity, AlertSeverity } from '@/types'

describe('type imports', () => {
  it('SecurityEvent type is importable', () => {
    const ev: Partial<SecurityEvent> = {
      id: 'test-id',
      event_type: 'login_failure',
      severity: 'high',
      risk_score: 75,
      is_processed: false,
    }
    expect(ev.id).toBe('test-id')
    expect(ev.severity).toBe('high')
  })

  it('Alert type is importable', () => {
    const alert: Partial<Alert> = {
      id: 'alert-1',
      title: 'Brute Force Detected',
      severity: 'critical',
      status: 'open',
    }
    expect(alert.status).toBe('open')
  })
})

describe('severityWeight function', () => {
  it('returns correct weight for event severities', () => {
    expect(severityWeight('info')).toBe(0)
    expect(severityWeight('low')).toBe(1)
    expect(severityWeight('medium')).toBe(2)
    expect(severityWeight('high')).toBe(3)
    expect(severityWeight('critical')).toBe(4)
  })

  it('returns 0 for unknown severity', () => {
    expect(severityWeight('unknown' as EventSeverity)).toBe(0)
  })

  it('critical > high > medium', () => {
    expect(severityWeight('critical')).toBeGreaterThan(severityWeight('high'))
    expect(severityWeight('high')).toBeGreaterThan(severityWeight('medium'))
  })
})

describe('AlertStatus values', () => {
  it('accepts valid status values', () => {
    const statuses: AlertStatus[] = ['open', 'investigating', 'resolved', 'false_positive']
    expect(statuses).toHaveLength(4)
  })
})

describe('AlertSeverity values', () => {
  it('accepts valid severity values', () => {
    const sevs: AlertSeverity[] = ['low', 'medium', 'high', 'critical']
    expect(sevs).toHaveLength(4)
  })
})
