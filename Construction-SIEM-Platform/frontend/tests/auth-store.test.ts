import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

// Payload: {"sub":"tanaka","role":"analyst"} → base64url without padding
const FAKE_TOKEN = 'header.eyJzdWIiOiJ0YW5ha2EiLCJyb2xlIjoiYW5hbHlzdCJ9.sig'
const FAKE_REFRESH = 'refresh-token-abc'
const NEW_TOKEN = 'header.eyJzdWIiOiJuZXciLCJyb2xlIjoiYW5hbHlzdCJ9.sig'
const NEW_REFRESH = 'new-refresh-xyz'

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  },
}))

describe('useAuthStore (CSIEM)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('initial state: not authenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.refreshToken).toBeNull()
  })

  it('login sets token, refreshToken and decoded user', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce({
      access_token: FAKE_TOKEN,
      refresh_token: FAKE_REFRESH,
      token_type: 'bearer',
    })
    const store = useAuthStore()
    await store.login('tanaka', 'pass')
    expect(store.token).toBe(FAKE_TOKEN)
    expect(store.refreshToken).toBe(FAKE_REFRESH)
    expect(store.isAuthenticated).toBe(true)
    expect(localStorage.getItem('auth_token')).toBe(FAKE_TOKEN)
    expect(localStorage.getItem('auth_refresh')).toBe(FAKE_REFRESH)
  })

  it('logout clears all state even when API fails', async () => {
    vi.mocked(authApi.logout).mockRejectedValueOnce(new Error('Server error'))
    const store = useAuthStore()
    store.token = FAKE_TOKEN
    store.refreshToken = FAKE_REFRESH
    await store.logout()
    expect(store.token).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.user).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem('auth_token')).toBeNull()
  })

  it('logout succeeds normally', async () => {
    vi.mocked(authApi.logout).mockResolvedValueOnce(undefined)
    const store = useAuthStore()
    store.token = FAKE_TOKEN
    await store.logout()
    expect(store.token).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('checkAuth restores session from localStorage', () => {
    localStorage.setItem('auth_token', FAKE_TOKEN)
    localStorage.setItem('auth_refresh', FAKE_REFRESH)
    const store = useAuthStore()
    store.checkAuth()
    expect(store.token).toBe(FAKE_TOKEN)
    expect(store.refreshToken).toBe(FAKE_REFRESH)
    expect(store.isAuthenticated).toBe(true)
  })

  it('checkAuth does nothing when localStorage is empty', () => {
    const store = useAuthStore()
    store.checkAuth()
    expect(store.token).toBeNull()
  })

  it('checkAuth does nothing when only refresh token exists', () => {
    localStorage.setItem('auth_refresh', FAKE_REFRESH)
    const store = useAuthStore()
    store.checkAuth()
    expect(store.token).toBeNull()
  })

  it('refreshAuthToken updates tokens', async () => {
    vi.mocked(authApi.refresh).mockResolvedValueOnce({
      access_token: NEW_TOKEN,
      refresh_token: NEW_REFRESH,
      token_type: 'bearer',
    })
    const store = useAuthStore()
    store.token = FAKE_TOKEN
    store.refreshToken = FAKE_REFRESH
    await store.refreshAuthToken()
    expect(store.token).toBe(NEW_TOKEN)
    expect(store.refreshToken).toBe(NEW_REFRESH)
    expect(localStorage.getItem('auth_token')).toBe(NEW_TOKEN)
  })

  it('refreshAuthToken throws when no refresh token', async () => {
    const store = useAuthStore()
    await expect(store.refreshAuthToken()).rejects.toThrow('No refresh token')
  })

  it('isAuthenticated reflects token state', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    store.token = FAKE_TOKEN
    expect(store.isAuthenticated).toBe(true)
    store.token = null
    expect(store.isAuthenticated).toBe(false)
  })
})
