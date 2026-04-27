import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/auth', () => ({
  authApi: { login: vi.fn(), logout: vi.fn(), refresh: vi.fn() },
}))

import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const MOCK_USER = { id: 'u1', username: 'sato', email: 'sato@example.com', displayName: '佐藤 一郎' }
const MOCK_TOKENS = { accessToken: 'at-abc', refreshToken: 'rt-xyz', user: MOCK_USER }

describe('useAuthStore (BCP)', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('成功時にトークン・ユーザーをセットしlocalStorageへ永続化する', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      const store = useAuthStore()
      const ok = await store.login({ username: 'sato', password: 'pass123' })
      expect(ok).toBe(true)
      expect(store.accessToken).toBe('at-abc')
      expect(store.refreshToken).toBe('rt-xyz')
      expect(store.user).toEqual(MOCK_USER)
      expect(store.isAuthenticated).toBe(true)
      const stored = JSON.parse(localStorage.getItem('auth')!)
      expect(stored.accessToken).toBe('at-abc')
      expect(stored.user.username).toBe('sato')
    })

    it('失敗時にfalseを返しstateを変更しない', async () => {
      vi.mocked(authApi.login).mockRejectedValue(new Error('unauthorized'))
      const store = useAuthStore()
      const ok = await store.login({ username: 'bad', password: 'wrong' })
      expect(ok).toBe(false)
      expect(store.accessToken).toBeNull()
      expect(store.isAuthenticated).toBe(false)
    })

    it('loading フラグが正しく制御される', async () => {
      let resolveFn!: () => void
      vi.mocked(authApi.login).mockReturnValue(
        new Promise<typeof MOCK_TOKENS>((r) => { resolveFn = () => r(MOCK_TOKENS) }),
      )
      const store = useAuthStore()
      const p = store.login({ username: 'sato', password: 'pass' })
      expect(store.loading).toBe(true)
      resolveFn()
      await p
      expect(store.loading).toBe(false)
    })
  })

  describe('logout', () => {
    it('ログアウトでstate・localStorageをクリアする', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      vi.mocked(authApi.logout).mockResolvedValue(undefined)
      const store = useAuthStore()
      await store.login({ username: 'sato', password: 'pass' })
      await store.logout()
      expect(store.user).toBeNull()
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(localStorage.getItem('auth')).toBeNull()
    })

    it('APIエラーでもstateをクリアする', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      vi.mocked(authApi.logout).mockRejectedValue(new Error('network'))
      const store = useAuthStore()
      await store.login({ username: 'sato', password: 'pass' })
      await store.logout()
      expect(store.accessToken).toBeNull()
    })
  })

  describe('refresh', () => {
    it('refreshTokenがなければfalseを返す', async () => {
      const store = useAuthStore()
      const ok = await store.refresh()
      expect(ok).toBe(false)
    })

    it('成功時にaccessTokenを更新する', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      vi.mocked(authApi.refresh).mockResolvedValue({ accessToken: 'at-new' })
      const store = useAuthStore()
      await store.login({ username: 'sato', password: 'pass' })
      const ok = await store.refresh()
      expect(ok).toBe(true)
      expect(store.accessToken).toBe('at-new')
    })

    it('失敗時にログアウトしfalseを返す', async () => {
      vi.mocked(authApi.login).mockResolvedValue(MOCK_TOKENS)
      vi.mocked(authApi.refresh).mockRejectedValue(new Error('expired'))
      vi.mocked(authApi.logout).mockResolvedValue(undefined)
      const store = useAuthStore()
      await store.login({ username: 'sato', password: 'pass' })
      const ok = await store.refresh()
      expect(ok).toBe(false)
      expect(store.accessToken).toBeNull()
    })
  })

  describe('checkAuth（同期）', () => {
    it('localStorageに認証情報がなければfalseを返す', () => {
      const store = useAuthStore()
      const ok = store.checkAuth()
      expect(ok).toBe(false)
    })

    it('localStorageに有効な認証情報があればtrueを返す', () => {
      localStorage.setItem(
        'auth',
        JSON.stringify({ user: MOCK_USER, accessToken: 'at-stored', refreshToken: 'rt-stored' }),
      )
      setActivePinia(createPinia())
      const store = useAuthStore()
      const ok = store.checkAuth()
      expect(ok).toBe(true)
      expect(store.accessToken).toBe('at-stored')
    })

    it('localStorageの不正なJSONは無視してfalseを返す', () => {
      localStorage.setItem('auth', 'invalid-json{{{')
      setActivePinia(createPinia())
      const store = useAuthStore()
      const ok = store.checkAuth()
      expect(ok).toBe(false)
      expect(localStorage.getItem('auth')).toBeNull()
    })
  })

  describe('loadFromStorage（ストア生成時の初期化）', () => {
    it('localStorageに認証情報があればストア生成時に復元する', () => {
      localStorage.setItem(
        'auth',
        JSON.stringify({ user: MOCK_USER, accessToken: 'at-init', refreshToken: 'rt-init' }),
      )
      setActivePinia(createPinia())
      const store = useAuthStore()
      expect(store.accessToken).toBe('at-init')
      expect(store.user).toEqual(MOCK_USER)
      expect(store.isAuthenticated).toBe(true)
    })
  })
})
