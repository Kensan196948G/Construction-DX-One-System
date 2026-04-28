import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRolesStore } from '@/stores/roles'
import { rolesApi } from '@/api/roles'
import type { Role } from '@/types'

vi.mock('@/api/roles', () => ({
  rolesApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    assign: vi.fn(),
    revoke: vi.fn(),
  },
}))

const mockRole: Role = {
  id: 'r1',
  name: 'site-manager',
  description: '現場管理者ロール',
  permissions: ['read:reports', 'write:incidents'],
  is_privileged: false,
  created_at: '2026-04-01T00:00:00Z',
  user_count: 3,
}

const privilegedRole: Role = {
  id: 'r2',
  name: 'security-admin',
  description: 'セキュリティ管理者',
  permissions: ['*'],
  is_privileged: true,
  created_at: '2026-04-01T00:00:00Z',
  user_count: 1,
}

describe('useRolesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchRoles sets roles on success', async () => {
    vi.mocked(rolesApi.list).mockResolvedValueOnce([mockRole, privilegedRole])
    const store = useRolesStore()
    await store.fetchRoles()

    expect(store.roles).toHaveLength(2)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchRoles sets error on failure', async () => {
    vi.mocked(rolesApi.list).mockRejectedValueOnce(new Error('Server error'))
    const store = useRolesStore()
    await store.fetchRoles()

    expect(store.roles).toHaveLength(0)
    expect(store.error).toBe('Server error')
    expect(store.loading).toBe(false)
  })

  it('fetchRole sets selectedRole', async () => {
    vi.mocked(rolesApi.get).mockResolvedValueOnce(mockRole)
    const store = useRolesStore()
    const result = await store.fetchRole('r1')

    expect(result).toEqual(mockRole)
    expect(store.selectedRole).toEqual(mockRole)
  })

  it('fetchRole returns null on failure', async () => {
    vi.mocked(rolesApi.get).mockRejectedValueOnce(new Error('Not found'))
    const store = useRolesStore()
    const result = await store.fetchRole('nonexistent')

    expect(result).toBeNull()
    expect(store.error).toBe('Not found')
  })

  it('createRole prepends to roles list', async () => {
    vi.mocked(rolesApi.create).mockResolvedValueOnce(mockRole)
    const store = useRolesStore()
    const result = await store.createRole({ name: 'site-manager' })

    expect(result).toEqual(mockRole)
    expect(store.roles[0]).toEqual(mockRole)
  })

  it('createRole returns null on failure', async () => {
    vi.mocked(rolesApi.create).mockRejectedValueOnce(new Error('Duplicate'))
    const store = useRolesStore()
    const result = await store.createRole({ name: 'existing-role' })

    expect(result).toBeNull()
    expect(store.error).toBe('Duplicate')
  })

  it('updateRole replaces role in list and updates selectedRole', async () => {
    const updated = { ...mockRole, name: 'updated-manager' }
    vi.mocked(rolesApi.update).mockResolvedValueOnce(updated)
    const store = useRolesStore()
    store.roles = [mockRole]
    store.selectedRole = mockRole

    const result = await store.updateRole('r1', { name: 'updated-manager' })
    expect(result).toEqual(updated)
    expect(store.roles[0].name).toBe('updated-manager')
    expect(store.selectedRole?.name).toBe('updated-manager')
  })

  it('updateRole returns null on failure', async () => {
    vi.mocked(rolesApi.update).mockRejectedValueOnce(new Error('Update failed'))
    const store = useRolesStore()
    const result = await store.updateRole('r1', { name: 'fail' })

    expect(result).toBeNull()
    expect(store.error).toBe('Update failed')
  })

  it('deleteRole removes role from list', async () => {
    vi.mocked(rolesApi.delete).mockResolvedValueOnce(undefined)
    const store = useRolesStore()
    store.roles = [mockRole, privilegedRole]
    store.selectedRole = mockRole

    const result = await store.deleteRole('r1')
    expect(result).toBe(true)
    expect(store.roles).toHaveLength(1)
    expect(store.roles[0].id).toBe('r2')
    expect(store.selectedRole).toBeNull()
  })

  it('deleteRole returns false on failure', async () => {
    vi.mocked(rolesApi.delete).mockRejectedValueOnce(new Error('Cannot delete'))
    const store = useRolesStore()
    const result = await store.deleteRole('r1')

    expect(result).toBe(false)
    expect(store.error).toBe('Cannot delete')
  })

  it('assignRole updates assigned user ids', async () => {
    const updated = { ...mockRole, user_count: 4 }
    vi.mocked(rolesApi.assign).mockResolvedValueOnce(updated)
    const store = useRolesStore()
    store.roles = [mockRole]

    const result = await store.assignRole('r1', { user_id: 'u10' })
    expect(result).toEqual(updated)
    expect(store.assignedUserIds.get('r1')).toContain('u10')
  })

  it('assignRole does not duplicate user id', async () => {
    vi.mocked(rolesApi.assign).mockResolvedValueOnce(mockRole)
    const store = useRolesStore()
    store.roles = [mockRole]
    store.assignedUserIds.set('r1', ['u10'])

    await store.assignRole('r1', { user_id: 'u10' })
    expect(store.assignedUserIds.get('r1')?.filter((id) => id === 'u10')).toHaveLength(1)
  })

  it('revokeRole removes user from assignedUserIds', async () => {
    vi.mocked(rolesApi.revoke).mockResolvedValueOnce(undefined)
    const store = useRolesStore()
    store.assignedUserIds.set('r1', ['u10', 'u20'])

    const result = await store.revokeRole('r1', 'u10')
    expect(result).toBe(true)
    expect(store.assignedUserIds.get('r1')).not.toContain('u10')
    expect(store.assignedUserIds.get('r1')).toContain('u20')
  })

  it('privilegedRoles computed returns only privileged roles', async () => {
    vi.mocked(rolesApi.list).mockResolvedValueOnce([mockRole, privilegedRole])
    const store = useRolesStore()
    await store.fetchRoles()

    expect(store.privilegedRoles).toHaveLength(1)
    expect(store.privilegedRoles[0].name).toBe('security-admin')
  })

  it('regularRoles computed returns only non-privileged roles', async () => {
    vi.mocked(rolesApi.list).mockResolvedValueOnce([mockRole, privilegedRole])
    const store = useRolesStore()
    await store.fetchRoles()

    expect(store.regularRoles).toHaveLength(1)
    expect(store.regularRoles[0].name).toBe('site-manager')
  })
})
