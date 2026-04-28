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
  username: 'compliance_officer',
  email: 'co@example.com',
  display_name: 'コンプライアンス担当',
  role: 'compliance_officer',
}

const mockLoginResponse = {
  access_token: 'access-token-abc',
  refresh_token: 'refresh-token-xyz',
  user: mockUser,
}

describe('useAuthStore (GRC)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('initial state from empty localStorage is unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.accessToken).toBeNull()
  })

  it('login sets tokens and user', async () => {
    vi.mocked(authApi.login).mockResolvedValueOnce(mockLoginResponse)
    const store = useAuthStore()
    await store.login('compliance_officer', 'pass')

    expect(store.isAuthenticated).toBe(true)
    expect(store.user).toEqual(mockUser)
    expect(store.accessToken).toBe('access-token-abc')
    expect(localStorage.getItem('access_token')).toBe('access-token-abc')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-token-xyz')
  })

  it('login propagates API errors', async () => {
    vi.mocked(authApi.login).mockRejectedValueOnce(new Error('Invalid credentials'))
    const store = useAuthStore()
    await expect(store.login('bad', 'creds')).rejects.toThrow('Invalid credentials')
    expect(store.isAuthenticated).toBe(false)
  })

  it('logout clears all state and fires API', () => {
    vi.mocked(authApi.logout).mockResolvedValueOnce(undefined)
    const store = useAuthStore()
    store.accessToken = 'access-token-abc'
    store.refreshToken = 'refresh-token-xyz'
    store.user = mockUser

    store.logout()

    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.accessToken).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('logout without refreshToken does not call API', () => {
    const store = useAuthStore()
    store.accessToken = 'access-token-abc'
    store.logout()

    expect(authApi.logout).not.toHaveBeenCalled()
  })

  it('refresh updates access token', async () => {
    vi.mocked(authApi.refresh).mockResolvedValueOnce({
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
    })
    const store = useAuthStore()
    store.refreshToken = 'old-refresh'

    await store.refresh()
    expect(store.accessToken).toBe('new-access-token')
    expect(localStorage.getItem('access_token')).toBe('new-access-token')
  })

  it('refresh throws when no refresh token', async () => {
    const store = useAuthStore()
    await expect(store.refresh()).rejects.toThrow('No refresh token')
  })

  it('checkAuth returns true when token is valid', async () => {
    vi.mocked(authApi.me).mockResolvedValueOnce(mockUser)
    const store = useAuthStore()
    store.accessToken = 'access-token-abc'

    const result = await store.checkAuth()
    expect(result).toBe(true)
    expect(store.user).toEqual(mockUser)
  })

  it('checkAuth returns false when no access token', async () => {
    const store = useAuthStore()
    const result = await store.checkAuth()
    expect(result).toBe(false)
  })

  it('checkAuth retries with refresh on 401', async () => {
    vi.mocked(authApi.me)
      .mockRejectedValueOnce(new Error('401'))
      .mockResolvedValueOnce(mockUser)
    vi.mocked(authApi.refresh).mockResolvedValueOnce({
      access_token: 'new-access',
      refresh_token: 'new-refresh',
    })
    const store = useAuthStore()
    store.accessToken = 'expired-token'
    store.refreshToken = 'refresh-token'

    const result = await store.checkAuth()
    expect(result).toBe(true)
    expect(store.user).toEqual(mockUser)
  })

  it('checkAuth returns false when refresh also fails', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new Error('401'))
    vi.mocked(authApi.refresh).mockRejectedValueOnce(new Error('Refresh expired'))
    vi.mocked(authApi.logout).mockResolvedValueOnce(undefined)
    const store = useAuthStore()
    store.accessToken = 'expired-token'
    store.refreshToken = 'expired-refresh'

    const result = await store.checkAuth()
    expect(result).toBe(false)
    expect(store.isAuthenticated).toBe(false)
  })
})
