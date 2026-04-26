import { describe, it, expect, vi } from 'vitest'

vi.mock('axios', async () => {
  const actual = await vi.importActual<typeof import('axios')>('axios')
  return {
    default: {
      ...actual.default,
      create: vi.fn(() => ({
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      })),
    },
  }
})

describe('API client module', () => {
  it('can be imported without errors', async () => {
    const mod = await import('@/api/client')
    expect(mod.default).toBeDefined()
  })
})

describe('API modules', () => {
  it('eventsApi exports expected methods', async () => {
    const { eventsApi } = await import('@/api/events')
    expect(typeof eventsApi.list).toBe('function')
    expect(typeof eventsApi.get).toBe('function')
    expect(typeof eventsApi.ingest).toBe('function')
    expect(typeof eventsApi.bulkIngest).toBe('function')
    expect(typeof eventsApi.markProcessed).toBe('function')
  })

  it('alertsApi exports expected methods', async () => {
    const { alertsApi } = await import('@/api/alerts')
    expect(typeof alertsApi.list).toBe('function')
    expect(typeof alertsApi.get).toBe('function')
    expect(typeof alertsApi.create).toBe('function')
    expect(typeof alertsApi.updateStatus).toBe('function')
  })

  it('healthApi exports check method', async () => {
    const { healthApi } = await import('@/api/health')
    expect(typeof healthApi.check).toBe('function')
  })
})
