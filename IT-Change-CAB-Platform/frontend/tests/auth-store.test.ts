import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/auth', () => ({
  authApi: { login: vi.fn(), logout: vi.fn(), refresh: vi.fn() },
}))

import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const MOCK_USER = { id: 'u1', username: 'yamada', displayName: '山田 太郎', roles: ['admin'] }
const MOCK_TOKENS = { accessToken: 'at-abc', refreshToken: 'rt-xyz', user: MOCK_USER }

describe('useAuthStore (CAB)', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('成功時にトークン・ユーザーを設定しlocalStorageに保存する', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      const store = useAuthStore()
      const ok = await store.login('yamada', 'pass123')
      expect(ok).toBe(true)
      expect(store.accessToken).toBe('at-abc')
      expect(store.refreshToken).toBe('rt-xyz')
      expect(store.user).toEqual(MOCK_USER)
      expect(store.isAuthenticated).toBe(true)
      expect(localStorage.getItem('accessToken')).toBe('at-abc')
      expect(localStorage.getItem('refreshToken')).toBe('rt-xyz')
    })

    it('失敗時にfalseを返しトークンを設定しない', async () => {
      vi.mocked(authApi.login).mockRejectedValue(new Error('invalid credentials'))
      const store = useAuthStore()
      const ok = await store.login('bad', 'wrong')
      expect(ok).toBe(false)
      expect(store.accessToken).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.error).toBe('invalid credentials')
    })

    it('loading フラグが login 中に true になる', async () => {
      let resolveFn!: () => void
      vi.mocked(authApi.login).mockReturnValue(
        new Promise<typeof MOCK_TOKENS>((r) => { resolveFn = () => r(MOCK_TOKENS) }),
      )
      const store = useAuthStore()
      const p = store.login('yamada', 'pass')
      expect(store.loading).toBe(true)
      resolveFn()
      await p
      expect(store.loading).toBe(false)
    })
  })

  describe('logout', () => {
    it('トークン・ユーザー・localStorageをクリアする', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      vi.mocked(authApi.logout).mockResolvedValue(undefined)
      const store = useAuthStore()
      await store.login('yamada', 'pass')
      await store.logout()
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.user).toBeNull()
      expect(localStorage.getItem('accessToken')).toBeNull()
    })

    it('API エラーでもクリアを実行する', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      vi.mocked(authApi.logout).mockRejectedValue(new Error('network'))
      const store = useAuthStore()
      await store.login('yamada', 'pass')
      await store.logout()
      expect(store.accessToken).toBeNull()
    })
  })

  describe('refreshAccessToken', () => {
    it('refreshTokenがない場合はfalseを返す', async () => {
      const store = useAuthStore()
      const ok = await store.refreshAccessToken()
      expect(ok).toBe(false)
    })

    it('成功時に新しいaccessTokenを設定する', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      vi.mocked(authApi.refresh).mockResolvedValue({ accessToken: 'at-new', refreshToken: 'rt-new' })
      const store = useAuthStore()
      await store.login('yamada', 'pass')
      const ok = await store.refreshAccessToken()
      expect(ok).toBe(true)
      expect(store.accessToken).toBe('at-new')
      expect(store.refreshToken).toBe('rt-new')
    })

    it('失敗時にトークンをクリアしfalseを返す', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      vi.mocked(authApi.refresh).mockRejectedValue(new Error('expired'))
      const store = useAuthStore()
      await store.login('yamada', 'pass')
      const ok = await store.refreshAccessToken()
      expect(ok).toBe(false)
      expect(store.accessToken).toBeNull()
    })
  })

  describe('checkAuth', () => {
    it('localStorageにトークンがなければfalseを返す', async () => {
      const store = useAuthStore()
      const ok = await store.checkAuth()
      expect(ok).toBe(false)
    })

    it('両トークンがlocalStorageにあればrefreshを試みる', async () => {
      localStorage.setItem('accessToken', 'at-stored')
      localStorage.setItem('refreshToken', 'rt-stored')
      localStorage.setItem('authUser', JSON.stringify(MOCK_USER))
      vi.mocked(authApi.refresh).mockResolvedValue({ accessToken: 'at-fresh', refreshToken: 'rt-fresh' })
      const store = useAuthStore()
      const ok = await store.checkAuth()
      expect(ok).toBe(true)
      expect(store.accessToken).toBe('at-fresh')
    })

    it('refreshが失敗すればfalseを返す', async () => {
      localStorage.setItem('accessToken', 'at-stored')
      localStorage.setItem('refreshToken', 'rt-stored')
      vi.mocked(authApi.refresh).mockRejectedValue(new Error('expired'))
      const store = useAuthStore()
      const ok = await store.checkAuth()
      expect(ok).toBe(false)
    })
  })

  describe('isAuthenticated', () => {
    it('accessTokenとuserの両方がある場合にtrue', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      const store = useAuthStore()
      await store.login('yamada', 'pass')
      expect(store.isAuthenticated).toBe(true)
    })

    it('初期状態はfalse', () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
    })
  })
})
