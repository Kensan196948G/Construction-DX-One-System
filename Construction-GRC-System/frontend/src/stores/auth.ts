import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => !!accessToken.value)

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    accessToken.value = res.access_token
    refreshToken.value = res.refresh_token
    user.value = res.user
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
  }

  async function refresh() {
    if (!refreshToken.value) throw new Error('No refresh token')
    const res = await authApi.refresh(refreshToken.value)
    accessToken.value = res.access_token
    if (res.refresh_token) {
      refreshToken.value = res.refresh_token
      localStorage.setItem('refresh_token', res.refresh_token)
    }
    localStorage.setItem('access_token', res.access_token)
  }

  async function checkAuth(): Promise<boolean> {
    if (!accessToken.value) return false
    try {
      const userData = await authApi.me()
      user.value = userData
      return true
    } catch {
      try {
        await refresh()
        const userData = await authApi.me()
        user.value = userData
        return true
      } catch {
        logout()
        return false
      }
    }
  }

  function logout() {
    const rt = refreshToken.value
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    if (rt) {
      authApi.logout(rt).catch(() => {})
    }
  }

  return { user, accessToken, refreshToken, isAuthenticated, login, refresh, checkAuth, logout }
})
