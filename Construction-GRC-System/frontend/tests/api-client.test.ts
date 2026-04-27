import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

vi.mock('axios', async () => {
  const actual = await vi.importActual<typeof import('axios')>('axios')
  return {
    default: {
      ...actual.default,
      create: vi.fn(() => ({
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
        interceptors: {
          request: { use: vi.fn() },
          response: {
            use: vi.fn(),
          },
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
  it('risksApi exports expected methods', async () => {
    const { risksApi } = await import('@/api/risks')
    expect(typeof risksApi.list).toBe('function')
    expect(typeof risksApi.get).toBe('function')
    expect(typeof risksApi.create).toBe('function')
    expect(typeof risksApi.update).toBe('function')
    expect(typeof risksApi.delete).toBe('function')
  })

  it('complianceApi exports expected methods', async () => {
    const { complianceApi } = await import('@/api/compliance')
    expect(typeof complianceApi.list).toBe('function')
    expect(typeof complianceApi.get).toBe('function')
    expect(typeof complianceApi.create).toBe('function')
    expect(typeof complianceApi.update).toBe('function')
    expect(typeof complianceApi.delete).toBe('function')
  })

  it('auditsApi exports expected methods including createFinding', async () => {
    const { auditsApi } = await import('@/api/audits')
    expect(typeof auditsApi.list).toBe('function')
    expect(typeof auditsApi.get).toBe('function')
    expect(typeof auditsApi.create).toBe('function')
    expect(typeof auditsApi.update).toBe('function')
    expect(typeof auditsApi.delete).toBe('function')
    expect(typeof auditsApi.listFindings).toBe('function')
    expect(typeof auditsApi.createFinding).toBe('function')
  })

  it('healthApi exports check method', async () => {
    const { healthApi } = await import('@/api/health')
    expect(typeof healthApi.check).toBe('function')
  })
})
