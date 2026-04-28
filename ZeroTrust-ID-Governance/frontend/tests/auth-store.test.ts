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

// Build a minimal valid JWT: header.payload.signature
function makeJwt(payload: Record<string, unknown>): string {
  const encoded = btoa(JSON.stringify(payload))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
  return `eyJhbGciOiJIUzI1NiJ9.${encoded}.sig`
}

const mockTokenResponse = {
  access_token: makeJwt({ sub: 'yamada', role: 'admin' }),
  refresh_token: 'refresh-token-xyz',
  token_type: 'bearer',
}

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('initial state is unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
  })

  it('login sets token, user, and persists to localStorage', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce(mockTokenResponse)
    const store = useAuthStore()
    await store.login('yamada', 'password123')

    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe(mockTokenResponse.access_token)
    expect(store.user?.username).toBe('yamada')
    expect(store.user?.role).toBe('admin')
    expect(localStorage.getItem('auth_token')).toBe(mockTokenResponse.access_token)
  })

  it('login propagates errors', async () => {
    vi.mocked(authApi.login).mockRejectedValueOnce(new Error('Unauthorized'))
    const store = useAuthStore()
    await expect(store.login('bad', 'creds')).rejects.toThrow('Unauthorized')
    expect(store.isAuthenticated).toBe(false)
  })

  it('logout clears state and localStorage', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce(mockTokenResponse)
    vi.mocked(authApi.logout).mockResolvedValueOnce(undefined)
    const store = useAuthStore()
    await store.login('yamada', 'password123')
    await store.logout()

    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(localStorage.getItem('auth_token')).toBeNull()
  })

  it('logout clears state even if API call fails', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce(mockTokenResponse)
    vi.mocked(authApi.logout).mockRejectedValueOnce(new Error('Network error'))
    const store = useAuthStore()
    await store.login('yamada', 'password123')
    await store.logout()

    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBeNull()
  })

  it('checkAuth restores state from localStorage', () => {
    localStorage.setItem('auth_token', mockTokenResponse.access_token)
    localStorage.setItem('auth_refresh', mockTokenResponse.refresh_token)
    const store = useAuthStore()
    store.checkAuth()

    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.username).toBe('yamada')
  })

  it('checkAuth does nothing when localStorage is empty', () => {
    const store = useAuthStore()
    store.checkAuth()
    expect(store.isAuthenticated).toBe(false)
  })

  it('refreshAuthToken updates tokens', async () => {
    const newToken = makeJwt({ sub: 'yamada', role: 'viewer' })
    vi.mocked(authApi.refresh).mockResolvedValueOnce({
      access_token: newToken,
      refresh_token: 'new-refresh',
      token_type: 'bearer',
    })
    const store = useAuthStore()
    store.token = mockTokenResponse.access_token
    // @ts-expect-error - accessing private ref
    store.refreshToken = mockTokenResponse.refresh_token

    await store.refreshAuthToken()
    expect(store.token).toBe(newToken)
    expect(store.user?.role).toBe('viewer')
  })

  it('refreshAuthToken throws when no refresh token', async () => {
    const store = useAuthStore()
    await expect(store.refreshAuthToken()).rejects.toThrow('No refresh token')
  })
})
