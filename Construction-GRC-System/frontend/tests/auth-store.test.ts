import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
  },
}))

const mockUser = {
  id: 'u1',
  username: 'tanaka',
  email: 'tanaka@example.com',
  display_name: '田中 太郎',
  role: 'admin',
}

const mockLoginResponse = {
  access_token: 'access-token-abc',
  refresh_token: 'refresh-token-xyz',
  user: mockUser,
}

describe('useAuthStore (CGRC)', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initial state: not authenticated without localStorage tokens', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.accessToken).toBeNull()
  })

  it('initializes accessToken from localStorage', () => {
    localStorage.setItem('access_token', 'stored-token')
    localStorage.setItem('refresh_token', 'stored-refresh')
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.accessToken).toBe('stored-token')
    expect(store.isAuthenticated).toBe(true)
  })

  it('login sets accessToken, refreshToken and user', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse)
    const store = useAuthStore()
    await store.login('tanaka', 'pass')
    expect(store.accessToken).toBe('access-token-abc')
    expect(store.refreshToken).toBe('refresh-token-xyz')
    expect(store.user?.username).toBe('tanaka')
    expect(store.isAuthenticated).toBe(true)
    expect(localStorage.getItem('access_token')).toBe('access-token-abc')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-token-xyz')
  })

  it('refresh updates accessToken', async () => {
    vi.mocked(authApi.refresh).mockResolvedValueOnce({
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
    })
    const store = useAuthStore()
    store.accessToken = 'old-token'
    store.refreshToken = 'refresh-token-xyz'
    await store.refresh()
    expect(store.accessToken).toBe('new-access-token')
    expect(localStorage.getItem('access_token')).toBe('new-access-token')
  })

  it('refresh throws when no refresh token', async () => {
    const store = useAuthStore()
    store.refreshToken = null
    await expect(store.refresh()).rejects.toThrow('No refresh token')
  })

  it('checkAuth returns false when no accessToken', async () => {
    const store = useAuthStore()
    const result = await store.checkAuth()
    expect(result).toBe(false)
  })

  it('checkAuth returns true when me() succeeds', async () => {
    vi.mocked(authApi.me).mockResolvedValueOnce(mockUser)
    const store = useAuthStore()
    store.accessToken = 'valid-token'
    const result = await store.checkAuth()
    expect(result).toBe(true)
    expect(store.user?.username).toBe('tanaka')
  })

  it('checkAuth retries with refresh when me() fails initially', async () => {
    vi.mocked(authApi.me)
      .mockRejectedValueOnce(new Error('Unauthorized'))
      .mockResolvedValueOnce(mockUser)
    vi.mocked(authApi.refresh).mockResolvedValueOnce({
      access_token: 'new-token',
      refresh_token: 'new-refresh',
    })
    const store = useAuthStore()
    store.accessToken = 'expired-token'
    store.refreshToken = 'refresh-token'
    const result = await store.checkAuth()
    expect(result).toBe(true)
    expect(store.user?.username).toBe('tanaka')
  })

  it('checkAuth returns false and logs out when both me() and refresh fail', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new Error('Unauthorized'))
    vi.mocked(authApi.refresh).mockRejectedValueOnce(new Error('Refresh failed'))
    vi.mocked(authApi.logout).mockResolvedValue(undefined)
    const store = useAuthStore()
    store.accessToken = 'expired-token'
    store.refreshToken = 'bad-refresh'
    const result = await store.checkAuth()
    expect(result).toBe(false)
    expect(store.accessToken).toBeNull()
  })

  it('logout clears all state and localStorage', () => {
    vi.mocked(authApi.logout).mockResolvedValue(undefined)
    const store = useAuthStore()
    store.accessToken = 'token'
    store.refreshToken = 'refresh'
    store.user = mockUser
    localStorage.setItem('access_token', 'token')
    localStorage.setItem('refresh_token', 'refresh')
    store.logout()
    expect(store.accessToken).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.user).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })

  it('logout skips API call when no refresh token', () => {
    const store = useAuthStore()
    store.accessToken = 'token'
    store.refreshToken = null
    store.logout()
    expect(authApi.logout).not.toHaveBeenCalled()
    expect(store.accessToken).toBeNull()
  })

  it('isAuthenticated reflects accessToken state', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    store.accessToken = 'token'
    expect(store.isAuthenticated).toBe(true)
    store.accessToken = null
    expect(store.isAuthenticated).toBe(false)
  })
})
