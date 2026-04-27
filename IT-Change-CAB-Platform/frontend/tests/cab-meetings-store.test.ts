import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCabMeetingsStore } from '@/stores/cabMeetings'
import { cabMeetingsApi } from '@/api/cabMeetings'
import type { CabMeeting } from '@/types'

vi.mock('@/api/cabMeetings', () => ({
  cabMeetingsApi: {
    list: vi.fn(),
  },
}))

const mockMeeting: CabMeeting = {
  id: 'm1',
  meetingNumber: 'CAB-2026-001',
  title: '月次 CAB 定例',
  status: 'scheduled',
  scheduledAt: '2026-05-10T10:00:00Z',
  facilitator: 'Bob',
  rfcCount: 3,
  createdAt: '2026-04-01T00:00:00Z',
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useCabMeetingsStore', () => {
  it('fetchMeetings sets meetings on success', async () => {
    vi.mocked(cabMeetingsApi.list).mockResolvedValueOnce([mockMeeting])
    const store = useCabMeetingsStore()
    await store.fetchMeetings()
    expect(store.meetings).toHaveLength(1)
    expect(store.meetings[0].meetingNumber).toBe('CAB-2026-001')
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchMeetings passes status filter', async () => {
    vi.mocked(cabMeetingsApi.list).mockResolvedValueOnce([])
    const store = useCabMeetingsStore()
    await store.fetchMeetings('scheduled')
    expect(cabMeetingsApi.list).toHaveBeenCalledWith('scheduled')
  })

  it('fetchMeetings sets error on failure', async () => {
    vi.mocked(cabMeetingsApi.list).mockRejectedValueOnce(new Error('Server error'))
    const store = useCabMeetingsStore()
    await store.fetchMeetings()
    expect(store.meetings).toHaveLength(0)
    expect(store.error).toBe('Server error')
  })

  it('scheduledMeetings returns only scheduled', () => {
    const store = useCabMeetingsStore()
    store.meetings = [
      mockMeeting,
      { ...mockMeeting, id: 'm2', status: 'completed' },
      { ...mockMeeting, id: 'm3', status: 'scheduled' },
      { ...mockMeeting, id: 'm4', status: 'cancelled' },
    ]
    expect(store.scheduledMeetings()).toHaveLength(2)
  })

  it('completedMeetings returns only completed', () => {
    const store = useCabMeetingsStore()
    store.meetings = [
      mockMeeting,
      { ...mockMeeting, id: 'm2', status: 'completed' },
      { ...mockMeeting, id: 'm3', status: 'completed' },
    ]
    expect(store.completedMeetings()).toHaveLength(2)
  })

  it('initial state is empty', () => {
    const store = useCabMeetingsStore()
    expect(store.meetings).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchMeetings without status calls api with undefined', async () => {
    vi.mocked(cabMeetingsApi.list).mockResolvedValueOnce([mockMeeting])
    const store = useCabMeetingsStore()
    await store.fetchMeetings()
    expect(cabMeetingsApi.list).toHaveBeenCalledWith(undefined)
  })

  it('loading flag is true during fetch', async () => {
    let resolvePromise!: (v: CabMeeting[]) => void
    vi.mocked(cabMeetingsApi.list).mockReturnValueOnce(
      new Promise<CabMeeting[]>((res) => { resolvePromise = res }),
    )
    const store = useCabMeetingsStore()
    const fetchPromise = store.fetchMeetings()
    expect(store.loading).toBe(true)
    resolvePromise([mockMeeting])
    await fetchPromise
    expect(store.loading).toBe(false)
  })
})
