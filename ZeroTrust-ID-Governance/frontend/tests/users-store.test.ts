import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUsersStore } from '@/stores/users'
import { usersApi } from '@/api/users'

vi.mock('@/api/users', () => ({
  usersApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    updateStatus: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockUser = {
  id: 'u1',
  username: 'tanaka',
  full_name: '田中 太郎',
  email: 'tanaka@example.com',
  user_type: 'employee' as const,
  status: 'active' as const,
  department: '情報システム部',
  created_at: '2026-04-01T00:00:00Z',
  last_login_at: '2026-04-25T09:00:00Z',
  mfa_enabled: true,
  risk_score: 10,
}

describe('useUsersStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchUsers sets users on success', async () => {
    vi.mocked(usersApi.list).mockResolvedValueOnce([mockUser])
    const store = useUsersStore()
    await store.fetchUsers()
    expect(store.users).toHaveLength(1)
    expect(store.users[0].username).toBe('tanaka')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchUsers sets error on failure', async () => {
    vi.mocked(usersApi.list).mockRejectedValueOnce(new Error('Network error'))
    const store = useUsersStore()
    await store.fetchUsers()
    expect(store.users).toHaveLength(0)
    expect(store.error).toBe('Network error')
    expect(store.loading).toBe(false)
  })

  it('fetchUsers passes userType and status filters', async () => {
    vi.mocked(usersApi.list).mockResolvedValueOnce([mockUser])
    const store = useUsersStore()
    await store.fetchUsers('employee', 'active')
    expect(usersApi.list).toHaveBeenCalledWith('employee', 'active')
  })

  it('createUser prepends to users list', async () => {
    vi.mocked(usersApi.create).mockResolvedValueOnce(mockUser)
    const store = useUsersStore()
    const result = await store.createUser({ username: 'tanaka', full_name: '田中 太郎', email: 'tanaka@example.com' })
    expect(result).toEqual(mockUser)
    expect(store.users[0]).toEqual(mockUser)
  })

  it('createUser returns null on failure', async () => {
    vi.mocked(usersApi.create).mockRejectedValueOnce(new Error('Validation error'))
    const store = useUsersStore()
    const result = await store.createUser({ username: '', full_name: '', email: '' })
    expect(result).toBeNull()
    expect(store.error).toBe('Validation error')
  })

  it('updateUserStatus replaces user in list', async () => {
    const updated = { ...mockUser, status: 'locked' as const }
    vi.mocked(usersApi.updateStatus).mockResolvedValueOnce(updated)
    const store = useUsersStore()
    store.users = [mockUser]
    const result = await store.updateUserStatus('u1', 'locked')
    expect(result).toBe(true)
    expect(store.users[0].status).toBe('locked')
  })

  it('updateUserStatus returns false on failure', async () => {
    vi.mocked(usersApi.updateStatus).mockRejectedValueOnce(new Error('Not found'))
    const store = useUsersStore()
    const result = await store.updateUserStatus('nonexistent', 'locked')
    expect(result).toBe(false)
    expect(store.error).toBe('Not found')
  })

  it('activeUsers returns only active users', () => {
    const store = useUsersStore()
    store.users = [
      mockUser,
      { ...mockUser, id: 'u2', status: 'locked' as const },
      { ...mockUser, id: 'u3', status: 'disabled' as const },
    ]
    expect(store.activeUsers()).toHaveLength(1)
    expect(store.activeUsers()[0].id).toBe('u1')
  })

  it('lockedUsers returns only locked users', () => {
    const store = useUsersStore()
    store.users = [
      mockUser,
      { ...mockUser, id: 'u2', status: 'locked' as const },
    ]
    expect(store.lockedUsers()).toHaveLength(1)
    expect(store.lockedUsers()[0].id).toBe('u2')
  })
})
