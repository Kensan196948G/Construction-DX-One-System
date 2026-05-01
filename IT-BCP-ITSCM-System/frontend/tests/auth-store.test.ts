import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import type { LoginResponse } from '@/types'

vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
  },
}))

const mockLoginResponse: LoginResponse = {
  accessToken: 'bcp-access-token',
  refreshToken: 'bcp-refresh-token',
  user: { id: 'u1', username: 'admin', email: 'admin@miraikensetu.co.jp' },
}

describe('BCP Auth Store', () => {
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
    const result = await store.login({ username: 'admin', password: 'Admin@1234' })
    expect(result).toBe(true)
    expect(store.isAuthenticated).toBe(true)
    expect(store.accessToken).toBe('bcp-access-token')
    expect(store.user?.username).toBe('admin')
  })

  it('login 失敗時に false を返す', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('401'))
    const store = useAuthStore()
    const result = await store.login({ username: 'wrong', password: 'wrong' })
    expect(result).toBe(false)
    expect(store.isAuthenticated).toBe(false)
  })

  it('localStorage にトークンを永続化する', async () => {
    vi.mocked(authApi.login).mockResolvedValue(mockLoginResponse)
    const store = useAuthStore()
    await store.login({ username: 'admin', password: 'Admin@1234' })
    const stored = JSON.parse(localStorage.getItem('auth') ?? '{}')
    expect(stored.accessToken).toBe('bcp-access-token')
    expect(stored.user?.username).toBe('admin')
  })

  it('ストア初期化時に localStorage から認証状態を自動復元する', () => {
    localStorage.setItem('auth', JSON.stringify({
      user: { id: 'u1', username: 'admin' },
      accessToken: 'restored-token',
      refreshToken: 'restored-refresh',
    }))
    const store = useAuthStore()
    expect(store.accessToken).toBe('restored-token')
    expect(store.user?.username).toBe('admin')
    expect(store.isAuthenticated).toBe(true)
  })

  it('破損した localStorage データを安全に処理する', () => {
    localStorage.setItem('auth', 'invalid-json{{{')
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(localStorage.getItem('auth')).toBeNull()
  })

  it('login 中は loading が true になる', async () => {
    let resolveFn: (v: LoginResponse) => void
    vi.mocked(authApi.login).mockReturnValue(new Promise(r => { resolveFn = r }))
    const store = useAuthStore()
    const loginPromise = store.login({ username: 'admin', password: 'Admin@1234' })
    expect(store.loading).toBe(true)
    resolveFn!(mockLoginResponse)
    await loginPromise
    expect(store.loading).toBe(false)
  })
})
