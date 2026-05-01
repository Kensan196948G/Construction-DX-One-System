import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
  },
}))

const mockLoginResponse = {
  accessToken: 'mock-access-token',
  refreshToken: 'mock-refresh-token',
  user: { id: 'u1', username: 'admin', role: 'admin' },
}

describe('CAB Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('初期状態が未認証である', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.accessToken).toBeNull()
  })

  it('login 成功時に認証状態になる', async () => {
    vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)
    const store = useAuthStore()
    const result = await store.login('admin', 'Admin@1234')
    expect(result).toBe(true)
    expect(store.isAuthenticated).toBe(true)
    expect(store.accessToken).toBe('mock-access-token')
    expect(store.user?.username).toBe('admin')
  })

  it('login 失敗時に error が設定される', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid credentials'))
    const store = useAuthStore()
    const result = await store.login('wrong', 'wrong')
    expect(result).toBe(false)
    expect(store.isAuthenticated).toBe(false)
    expect(store.error).toBeTruthy()
  })

  it('logout 後に認証状態がクリアされる', async () => {
    vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)
    vi.mocked(authApi.logout).mockResolvedValue(undefined)
    const store = useAuthStore()
    await store.login('admin', 'Admin@1234')
    expect(store.isAuthenticated).toBe(true)
    await store.logout()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(store.accessToken).toBeNull()
  })

  it('checkAuth で localStorage のトークンが復元されリフレッシュされる', async () => {
    localStorage.setItem('accessToken', 'old-token')
    localStorage.setItem('refreshToken', 'old-refresh')
    localStorage.setItem('authUser', JSON.stringify({
      id: 'u1', username: 'admin', displayName: 'Admin', roles: ['admin']
    }))
    vi.mocked(authApi.refresh).mockResolvedValue({ accessToken: 'new-token', refreshToken: 'new-refresh' } as never)
    const store = useAuthStore()
    const ok = await store.checkAuth()
    expect(ok).toBe(true)
    expect(store.accessToken).toBe('new-token')
  })

  it('login 中は loading が true になる', async () => {
    let resolveFn: (v: unknown) => void
    vi.mocked(authApi.login).mockReturnValue(new Promise(r => { resolveFn = r }))
    const store = useAuthStore()
    const loginPromise = store.login('admin', 'Admin@1234')
    expect(store.loading).toBe(true)
    resolveFn!(mockLoginResponse)
    await loginPromise
    expect(store.loading).toBe(false)
  })
})
