import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usersApi } from '@/api/users'
import type { User, UserCreate, UserStatus, UserType } from '@/types'

export const useUsersStore = defineStore('users', () => {
  const users = ref<User[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchUsers(userType?: UserType, status?: UserStatus) {
    loading.value = true
    error.value = null
    try {
      users.value = await usersApi.list(userType, status)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load users'
    } finally {
      loading.value = false
    }
  }

  async function createUser(data: UserCreate): Promise<User | null> {
    try {
      const user = await usersApi.create(data)
      users.value.unshift(user)
      return user
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create user'
      return null
    }
  }

  async function updateUserStatus(id: string, status: UserStatus): Promise<boolean> {
    try {
      const updated = await usersApi.updateStatus(id, { status })
      const idx = users.value.findIndex((u) => u.id === id)
      if (idx !== -1) users.value.splice(idx, 1, updated)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update user status'
      return false
    }
  }

  const activeUsers = () => users.value.filter((u) => u.status === 'active')
  const lockedUsers = () => users.value.filter((u) => u.status === 'locked')

  return {
    users,
    loading,
    error,
    fetchUsers,
    createUser,
    updateUserStatus,
    activeUsers,
    lockedUsers,
  }
})
