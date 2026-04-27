import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRolesStore } from '@/stores/roles'
import { rolesApi } from '@/api/roles'

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

const mockRole = {
  id: 'r1',
  name: '工事管理者',
  description: '現場工事の管理権限',
  permissions: ['project:read', 'project:write'],
  is_privileged: false,
  created_at: '2026-04-01T00:00:00Z',
}

const mockPrivilegedRole = {
  id: 'r2',
  name: 'セキュリティ管理者',
  description: 'セキュリティ設定の全権限',
  permissions: ['security:all'],
  is_privileged: true,
  created_at: '2026-04-01T00:00:00Z',
}

describe('useRolesStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initial state: empty roles, no loading, no error', () => {
    const store = useRolesStore()
    expect(store.roles).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.selectedRole).toBeNull()
  })

  it('fetchRoles sets roles on success', async () => {
    vi.mocked(rolesApi.list).mockResolvedValueOnce([mockRole, mockPrivilegedRole])
    const store = useRolesStore()
    await store.fetchRoles()
    expect(store.roles).toHaveLength(2)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchRoles sets error on failure', async () => {
    vi.mocked(rolesApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useRolesStore()
    await store.fetchRoles()
    expect(store.roles).toHaveLength(0)
    expect(store.error).toBe('Network error')
    expect(store.loading).toBe(false)
  })

  it('fetchRole sets selectedRole on success', async () => {
    vi.mocked(rolesApi.get).mockResolvedValueOnce(mockRole)
    const store = useRolesStore()
    const result = await store.fetchRole('r1')
    expect(result).toEqual(mockRole)
    expect(store.selectedRole).toEqual(mockRole)
  })

  it('fetchRole returns null and sets error on failure', async () => {
    vi.mocked(rolesApi.get).mockRejectedValueOnce(new Error('Not found'))
    const store = useRolesStore()
    const result = await store.fetchRole('nonexistent')
    expect(result).toBeNull()
    expect(store.error).toBe('Not found')
  })

  it('createRole prepends role to list', async () => {
    vi.mocked(rolesApi.create).mockResolvedValueOnce(mockRole)
    const store = useRolesStore()
    const result = await store.createRole({ name: '工事管理者' })
    expect(result).toEqual(mockRole)
    expect(store.roles[0]).toEqual(mockRole)
  })

  it('createRole returns null on failure', async () => {
    vi.mocked(rolesApi.create).mockRejectedValueOnce(new Error('Validation error'))
    const store = useRolesStore()
    const result = await store.createRole({ name: '' })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation error')
  })

  it('updateRole replaces role in list', async () => {
    const updated = { ...mockRole, name: '更新管理者' }
    vi.mocked(rolesApi.update).mockResolvedValueOnce(updated)
    const store = useRolesStore()
    store.roles = [mockRole]
    const result = await store.updateRole('r1', { name: '更新管理者' })
    expect(result).toEqual(updated)
    expect(store.roles[0].name).toBe('更新管理者')
  })

  it('updateRole also updates selectedRole when it matches', async () => {
    const updated = { ...mockRole, name: '更新管理者' }
    vi.mocked(rolesApi.update).mockResolvedValueOnce(updated)
    const store = useRolesStore()
    store.roles = [mockRole]
    store.selectedRole = mockRole
    await store.updateRole('r1', { name: '更新管理者' })
    expect(store.selectedRole?.name).toBe('更新管理者')
  })

  it('updateRole returns null on failure', async () => {
    vi.mocked(rolesApi.update).mockRejectedValueOnce(new Error('Forbidden'))
    const store = useRolesStore()
    const result = await store.updateRole('r1', { name: '' })
    expect(result).toBeNull()
    expect(store.error).toBe('Forbidden')
  })

  it('deleteRole removes role from list', async () => {
    vi.mocked(rolesApi.delete).mockResolvedValueOnce(undefined)
    const store = useRolesStore()
    store.roles = [mockRole, mockPrivilegedRole]
    const result = await store.deleteRole('r1')
    expect(result).toBe(true)
    expect(store.roles).toHaveLength(1)
    expect(store.roles[0].id).toBe('r2')
  })

  it('deleteRole clears selectedRole when it matches', async () => {
    vi.mocked(rolesApi.delete).mockResolvedValueOnce(undefined)
    const store = useRolesStore()
    store.roles = [mockRole]
    store.selectedRole = mockRole
    await store.deleteRole('r1')
    expect(store.selectedRole).toBeNull()
  })

  it('deleteRole returns false on failure', async () => {
    vi.mocked(rolesApi.delete).mockRejectedValueOnce(new Error('Conflict'))
    const store = useRolesStore()
    const result = await store.deleteRole('r1')
    expect(result).toBe(false)
    expect(store.error).toBe('Conflict')
  })

  it('assignRole updates roles list and assignedUserIds', async () => {
    const updatedRole = { ...mockRole, permissions: ['project:read', 'project:write', 'user:assign'] }
    vi.mocked(rolesApi.assign).mockResolvedValueOnce(updatedRole)
    const store = useRolesStore()
    store.roles = [mockRole]
    const result = await store.assignRole('r1', { user_id: 'u1' })
    expect(result).toEqual(updatedRole)
    expect(store.assignedUserIds.get('r1')).toContain('u1')
  })

  it('assignRole does not duplicate userId in assignedUserIds', async () => {
    const updatedRole = { ...mockRole }
    vi.mocked(rolesApi.assign).mockResolvedValueOnce(updatedRole)
    const store = useRolesStore()
    store.roles = [mockRole]
    store.assignedUserIds.set('r1', ['u1'])
    await store.assignRole('r1', { user_id: 'u1' })
    expect(store.assignedUserIds.get('r1')).toHaveLength(1)
  })

  it('assignRole returns null on failure', async () => {
    vi.mocked(rolesApi.assign).mockRejectedValueOnce(new Error('User not found'))
    const store = useRolesStore()
    const result = await store.assignRole('r1', { user_id: 'nonexistent' })
    expect(result).toBeNull()
    expect(store.error).toBe('User not found')
  })

  it('revokeRole removes userId from assignedUserIds', async () => {
    vi.mocked(rolesApi.revoke).mockResolvedValueOnce(undefined)
    const store = useRolesStore()
    store.assignedUserIds.set('r1', ['u1', 'u2'])
    const result = await store.revokeRole('r1', 'u1')
    expect(result).toBe(true)
    expect(store.assignedUserIds.get('r1')).toEqual(['u2'])
  })

  it('revokeRole returns false on failure', async () => {
    vi.mocked(rolesApi.revoke).mockRejectedValueOnce(new Error('Not assigned'))
    const store = useRolesStore()
    const result = await store.revokeRole('r1', 'u1')
    expect(result).toBe(false)
    expect(store.error).toBe('Not assigned')
  })

  it('privilegedRoles computed returns only privileged roles', () => {
    const store = useRolesStore()
    store.roles = [mockRole, mockPrivilegedRole]
    expect(store.privilegedRoles).toHaveLength(1)
    expect(store.privilegedRoles[0].id).toBe('r2')
  })

  it('regularRoles computed returns only non-privileged roles', () => {
    const store = useRolesStore()
    store.roles = [mockRole, mockPrivilegedRole]
    expect(store.regularRoles).toHaveLength(1)
    expect(store.regularRoles[0].id).toBe('r1')
  })
})
