import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useExercisesStore } from '@/stores/exercises'
import { exercisesApi } from '@/api/exercises'
import type { Exercise } from '@/types'

vi.mock('@/api/exercises', () => ({
  exercisesApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    complete: vi.fn(),
  },
}))

const mockExercise: Exercise = {
  id: 'ex1',
  exerciseNumber: 'EX-2026-001',
  title: 'BCP 机上演習 2026',
  type: 'tabletop',
  status: 'planned',
  scheduledAt: '2026-06-01T09:00:00Z',
  completedAt: null,
  scenarioTitle: '大規模システム障害対応',
  participantsCount: 15,
  createdAt: '2026-05-01T10:00:00Z',
}

const mockCompleted: Exercise = {
  ...mockExercise,
  id: 'ex2',
  exerciseNumber: 'EX-2025-012',
  status: 'completed',
  completedAt: '2025-12-01T16:00:00Z',
}

const mockInProgress: Exercise = {
  ...mockExercise,
  id: 'ex3',
  exerciseNumber: 'EX-2026-002',
  status: 'in_progress',
}

describe('BCP Exercises Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初期状態が空配列である', () => {
    const store = useExercisesStore()
    expect(store.exercises).toHaveLength(0)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchExercises が演習一覧を取得する', async () => {
    vi.mocked(exercisesApi.list).mockResolvedValue([mockExercise, mockCompleted])
    const store = useExercisesStore()
    await store.fetchExercises()
    expect(store.exercises).toHaveLength(2)
    expect(store.exercises[0].exerciseNumber).toBe('EX-2026-001')
    expect(store.loading).toBe(false)
  })

  it('plannedExercises が planned ステータスのみ返す', async () => {
    vi.mocked(exercisesApi.list).mockResolvedValue([mockExercise, mockCompleted, mockInProgress])
    const store = useExercisesStore()
    await store.fetchExercises()
    const planned = store.plannedExercises()
    expect(planned).toHaveLength(1)
    expect(planned[0].status).toBe('planned')
  })

  it('completedExercises が completed ステータスのみ返す', async () => {
    vi.mocked(exercisesApi.list).mockResolvedValue([mockExercise, mockCompleted, mockInProgress])
    const store = useExercisesStore()
    await store.fetchExercises()
    const completed = store.completedExercises()
    expect(completed).toHaveLength(1)
    expect(completed[0].status).toBe('completed')
  })

  it('inProgressExercises が in_progress ステータスのみ返す', async () => {
    vi.mocked(exercisesApi.list).mockResolvedValue([mockExercise, mockCompleted, mockInProgress])
    const store = useExercisesStore()
    await store.fetchExercises()
    const inProgress = store.inProgressExercises()
    expect(inProgress).toHaveLength(1)
    expect(inProgress[0].status).toBe('in_progress')
  })

  it('API エラー時に error が設定される', async () => {
    vi.mocked(exercisesApi.list).mockRejectedValue(new Error('Network error'))
    const store = useExercisesStore()
    await store.fetchExercises()
    expect(store.error).toBeTruthy()
    expect(store.exercises).toHaveLength(0)
  })

  it('fetchExercises でステータスフィルタを渡せる', async () => {
    vi.mocked(exercisesApi.list).mockResolvedValue([mockExercise])
    const store = useExercisesStore()
    await store.fetchExercises('planned', 'tabletop')
    expect(exercisesApi.list).toHaveBeenCalledWith('planned', 'tabletop')
  })
})
