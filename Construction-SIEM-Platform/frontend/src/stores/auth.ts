import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { AuthUser } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  function decodeToken(t: string): AuthUser | null {
    try {
      const payload = t.split('.')[1]
      const decoded = JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')))
      return { username: decoded.sub ?? decoded.username ?? 'unknown', role: decoded.role }
    } catch {
      return null
    }
  }

  function persist() {
    if (token.value) {
      localStorage.setItem('auth_token', token.value)
      localStorage.setItem('auth_refresh', refreshToken.value ?? '')
    } else {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_refresh')
    }
  }

  function checkAuth() {
    const t = localStorage.getItem('auth_token')
    const rt = localStorage.getItem('auth_refresh')
    if (t && rt) {
      token.value = t
      refreshToken.value = rt
      user.value = decodeToken(t)
    }
  }

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    token.value = res.access_token
    refreshToken.value = res.refresh_token
    user.value = decodeToken(res.access_token)
    persist()
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // ignore logout API errors
    } finally {
      token.value = null
      refreshToken.value = null
      user.value = null
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_refresh')
    }
  }

  async function refreshAuthToken() {
    if (!refreshToken.value) throw new Error('No refresh token')
    const res = await authApi.refresh(refreshToken.value)
    token.value = res.access_token
    refreshToken.value = res.refresh_token
    user.value = decodeToken(res.access_token)
    persist()
  }

  return {
    user,
    token,
    refreshToken,
    isAuthenticated,
    login,
    logout,
    refreshAuthToken,
    checkAuth,
  }
})
