import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, LoginRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  function loadFromStorage() {
    const raw = localStorage.getItem('auth')
    if (!raw) return
    try {
      const data = JSON.parse(raw)
      user.value = data.user ?? null
      accessToken.value = data.accessToken ?? null
      refreshToken.value = data.refreshToken ?? null
    } catch {
      localStorage.removeItem('auth')
    }
  }

  function persist() {
    if (!accessToken.value || !refreshToken.value || !user.value) return
    localStorage.setItem(
      'auth',
      JSON.stringify({
        user: user.value,
        accessToken: accessToken.value,
        refreshToken: refreshToken.value,
      }),
    )
  }

  function clearStorage() {
    localStorage.removeItem('auth')
  }

  async function login(credentials: LoginRequest): Promise<boolean> {
    loading.value = true
    try {
      const res = await authApi.login(credentials)
      user.value = res.user
      accessToken.value = res.accessToken
      refreshToken.value = res.refreshToken
      persist()
      return true
    } catch {
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // ignore
    }
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    clearStorage()
  }

  async function refresh(): Promise<boolean> {
    if (!refreshToken.value) return false
    try {
      const res = await authApi.refresh(refreshToken.value)
      accessToken.value = res.accessToken
      persist()
      return true
    } catch {
      await logout()
      return false
    }
  }

  function checkAuth(): boolean {
    loadFromStorage()
    return isAuthenticated.value
  }

  loadFromStorage()

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    isAuthenticated,
    login,
    logout,
    refresh,
    checkAuth,
  }
})
