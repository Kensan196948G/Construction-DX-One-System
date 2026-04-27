import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { AuthUser } from '@/types'

const ACCESS_KEY = 'accessToken'
const REFRESH_KEY = 'refreshToken'
const USER_KEY = 'authUser'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  function persist() {
    if (accessToken.value) localStorage.setItem(ACCESS_KEY, accessToken.value)
    if (refreshToken.value) localStorage.setItem(REFRESH_KEY, refreshToken.value)
    if (user.value) localStorage.setItem(USER_KEY, JSON.stringify(user.value))
  }

  function restore() {
    const at = localStorage.getItem(ACCESS_KEY)
    const rt = localStorage.getItem(REFRESH_KEY)
    const u = localStorage.getItem(USER_KEY)
    if (at) accessToken.value = at
    if (rt) refreshToken.value = rt
    if (u) {
      try {
        user.value = JSON.parse(u) as AuthUser
      } catch {
        clear()
      }
    }
  }

  function clear() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    localStorage.removeItem(USER_KEY)
  }

  async function login(username: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const res = await authApi.login({ username, password })
      accessToken.value = res.accessToken
      refreshToken.value = res.refreshToken
      user.value = res.user
      persist()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Login failed'
      return false
    } finally {
      loading.value = false
    }
  }

  async function refreshAccessToken(): Promise<boolean> {
    const rt = refreshToken.value
    if (!rt) return false
    try {
      const res = await authApi.refresh(rt)
      accessToken.value = res.accessToken
      if (res.refreshToken) refreshToken.value = res.refreshToken
      persist()
      return true
    } catch {
      clear()
      return false
    }
  }

  async function checkAuth(): Promise<boolean> {
    restore()
    if (!accessToken.value || !refreshToken.value) {
      clear()
      return false
    }
    const ok = await refreshAccessToken()
    if (!ok) clear()
    return ok
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // ignore logout errors
    }
    clear()
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    error,
    isAuthenticated,
    login,
    logout,
    refreshAccessToken,
    checkAuth,
  }
})
