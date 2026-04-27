import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { rolesApi } from '@/api/roles'
import type { Role, RoleCreate, RoleUpdate, RoleAssign } from '@/types'

export const useRolesStore = defineStore('roles', () => {
  const roles = ref<Role[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedRole = ref<Role | null>(null)
  const assignedUserIds = ref<Map<string, string[]>>(new Map())

  async function fetchRoles() {
    loading.value = true
    error.value = null
    try {
      roles.value = await rolesApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load roles'
    } finally {
      loading.value = false
    }
  }

  async function fetchRole(id: string): Promise<Role | null> {
    try {
      const role = await rolesApi.get(id)
      selectedRole.value = role
      return role
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load role'
      return null
    }
  }

  async function createRole(data: RoleCreate): Promise<Role | null> {
    try {
      const role = await rolesApi.create(data)
      roles.value.unshift(role)
      return role
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create role'
      return null
    }
  }

  async function updateRole(id: string, data: RoleUpdate): Promise<Role | null> {
    try {
      const updated = await rolesApi.update(id, data)
      const idx = roles.value.findIndex((r) => r.id === id)
      if (idx !== -1) roles.value.splice(idx, 1, updated)
      if (selectedRole.value?.id === id) selectedRole.value = updated
      return updated
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update role'
      return null
    }
  }

  async function deleteRole(id: string): Promise<boolean> {
    try {
      await rolesApi.delete(id)
      roles.value = roles.value.filter((r) => r.id !== id)
      if (selectedRole.value?.id === id) selectedRole.value = null
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete role'
      return false
    }
  }

  async function assignRole(roleId: string, data: RoleAssign): Promise<Role | null> {
    try {
      const role = await rolesApi.assign(roleId, data)
      const current = assignedUserIds.value.get(roleId) || []
      if (!current.includes(data.user_id)) {
        current.push(data.user_id)
        assignedUserIds.value.set(roleId, current)
      }
      const idx = roles.value.findIndex((r) => r.id === roleId)
      if (idx !== -1) roles.value.splice(idx, 1, role)
      return role
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to assign role'
      return null
    }
  }

  async function revokeRole(roleId: string, userId: string): Promise<boolean> {
    try {
      await rolesApi.revoke(roleId, userId)
      const current = assignedUserIds.value.get(roleId) || []
      assignedUserIds.value.set(roleId, current.filter((id) => id !== userId))
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to revoke role'
      return false
    }
  }

  const privilegedRoles = computed(() => roles.value.filter((r) => r.is_privileged))
  const regularRoles = computed(() => roles.value.filter((r) => !r.is_privileged))

  return {
    roles,
    loading,
    error,
    selectedRole,
    assignedUserIds,
    fetchRoles,
    fetchRole,
    createRole,
    updateRole,
    deleteRole,
    assignRole,
    revokeRole,
    privilegedRoles,
    regularRoles,
  }
})
