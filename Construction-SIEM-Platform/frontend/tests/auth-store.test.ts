import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  },
}))

function makeJwt(payload: Record<string, unknown>): string {
  const encoded = btoa(JSON.stringify(payload))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
  return `eyJhbGciOiJIUzI1NiJ9.${encoded}.sig`
}

const mockTokenResponse = {
  access_token: makeJwt({ sub: 'siem_user', role: 'analyst' }),
  refresh_token: 'siem-refresh-token',
  token_type: 'bearer',
}

describe('useAuthStore (SIEM)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('initial state is unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
  })

  it('login sets token and user', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce(mockTokenResponse)
    const store = useAuthStore()
    await store.login('siem_user', 'pass')

    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.username).toBe('siem_user')
    expect(store.user?.role).toBe('analyst')
    expect(localStorage.getItem('auth_token')).toBe(mockTokenResponse.access_token)
  })

  it('login propagates errors', async () => {
    vi.mocked(authApi.login).mockRejectedValueOnce(new Error('Invalid credentials'))
    const store = useAuthStore()
    await expect(store.login('bad', 'creds')).rejects.toThrow('Invalid credentials')
  })

  it('logout clears all state', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce(mockTokenResponse)
    vi.mocked(authApi.logout).mockResolvedValueOnce(undefined)
    const store = useAuthStore()
    await store.login('siem_user', 'pass')
    await store.logout()

    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(localStorage.getItem('auth_token')).toBeNull()
  })

  it('logout clears state even when API fails', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce(mockTokenResponse)
    vi.mocked(authApi.logout).mockRejectedValueOnce(new Error('Network error'))
    const store = useAuthStore()
    await store.login('siem_user', 'pass')
    await store.logout()

    expect(store.isAuthenticated).toBe(false)
  })

  it('checkAuth restores state from localStorage', () => {
    localStorage.setItem('auth_token', mockTokenResponse.access_token)
    localStorage.setItem('auth_refresh', mockTokenResponse.refresh_token)
    const store = useAuthStore()
    store.checkAuth()

    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.username).toBe('siem_user')
  })

  it('checkAuth does nothing when localStorage is empty', () => {
    const store = useAuthStore()
    store.checkAuth()
    expect(store.isAuthenticated).toBe(false)
  })

  it('refreshAuthToken throws when no refresh token', async () => {
    const store = useAuthStore()
    await expect(store.refreshAuthToken()).rejects.toThrow('No refresh token')
  })
})
