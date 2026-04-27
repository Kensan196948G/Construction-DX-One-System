import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/exercises', () => ({
  exercisesApi: { list: vi.fn() },
}))

import { useExercisesStore } from '@/stores/exercises'
import { exercisesApi } from '@/api/exercises'
import type { Exercise } from '@/types'

const makeExercise = (overrides: Partial<Exercise> = {}): Exercise => ({
  id: 'ex1',
  exerciseNumber: 'EX-001',
  title: 'BCP訓練 2026年Q1',
  type: 'tabletop',
  status: 'planned',
  scheduledAt: '2026-05-10T09:00:00Z',
  completedAt: null,
  scenarioTitle: 'システム全停止シナリオ',
  participantsCount: 20,
  createdAt: '2026-04-01T00:00:00Z',
  ...overrides,
})

describe('useExercisesStore (BCP)', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('fetchExercises', () => {
    it('APIから訓練一覧を取得してstateに保存する', async () => {
      const exercises = [
        makeExercise(),
        makeExercise({ id: 'ex2', exerciseNumber: 'EX-002', status: 'completed' }),
      ]
      vi.mocked(exercisesApi.list).mockResolvedValue(exercises)
      const store = useExercisesStore()
      await store.fetchExercises()
      expect(store.exercises).toHaveLength(2)
      expect(store.exercises[0].exerciseNumber).toBe('EX-001')
    })

    it('フィルタ引数をAPIに渡す', async () => {
      vi.mocked(exercisesApi.list).mockResolvedValue([])
      const store = useExercisesStore()
      await store.fetchExercises('planned', 'tabletop')
      expect(exercisesApi.list).toHaveBeenCalledWith('planned', 'tabletop')
    })

    it('引数なしでもAPIを呼び出せる', async () => {
      vi.mocked(exercisesApi.list).mockResolvedValue([])
      const store = useExercisesStore()
      await store.fetchExercises()
      expect(exercisesApi.list).toHaveBeenCalledWith(undefined, undefined)
    })

    it('API失敗時にerrorをセットする', async () => {
      vi.mocked(exercisesApi.list).mockRejectedValue(new Error('サーバーエラー'))
      const store = useExercisesStore()
      await store.fetchExercises()
      expect(store.error).toBe('サーバーエラー')
      expect(store.exercises).toHaveLength(0)
    })

    it('loading フラグが取得中にtrueになる', async () => {
      let resolveFn!: () => void
      vi.mocked(exercisesApi.list).mockReturnValue(
        new Promise<Exercise[]>((r) => { resolveFn = () => r([]) }),
      )
      const store = useExercisesStore()
      const p = store.fetchExercises()
      expect(store.loading).toBe(true)
      resolveFn()
      await p
      expect(store.loading).toBe(false)
    })

    it('非Errorの例外はデフォルトメッセージをセットする', async () => {
      vi.mocked(exercisesApi.list).mockRejectedValue('unexpected')
      const store = useExercisesStore()
      await store.fetchExercises()
      expect(store.error).toBe('データ取得に失敗しました')
    })
  })

  describe('plannedExercises', () => {
    it('statusがplannedの訓練のみ返す', async () => {
      vi.mocked(exercisesApi.list).mockResolvedValue([
        makeExercise({ id: 'ex1', status: 'planned' }),
        makeExercise({ id: 'ex2', status: 'completed' }),
        makeExercise({ id: 'ex3', status: 'in_progress' }),
      ])
      const store = useExercisesStore()
      await store.fetchExercises()
      expect(store.plannedExercises()).toHaveLength(1)
      expect(store.plannedExercises()[0].id).toBe('ex1')
    })
  })

  describe('completedExercises', () => {
    it('statusがcompletedの訓練のみ返す', async () => {
      vi.mocked(exercisesApi.list).mockResolvedValue([
        makeExercise({ id: 'ex1', status: 'completed' }),
        makeExercise({ id: 'ex2', status: 'completed' }),
        makeExercise({ id: 'ex3', status: 'planned' }),
      ])
      const store = useExercisesStore()
      await store.fetchExercises()
      expect(store.completedExercises()).toHaveLength(2)
    })
  })

  describe('inProgressExercises', () => {
    it('statusがin_progressの訓練のみ返す', async () => {
      vi.mocked(exercisesApi.list).mockResolvedValue([
        makeExercise({ id: 'ex1', status: 'in_progress' }),
        makeExercise({ id: 'ex2', status: 'planned' }),
      ])
      const store = useExercisesStore()
      await store.fetchExercises()
      expect(store.inProgressExercises()).toHaveLength(1)
      expect(store.inProgressExercises()[0].status).toBe('in_progress')
    })
  })

  describe('初期状態', () => {
    it('exercises・error は空、loading は false', () => {
      const store = useExercisesStore()
      expect(store.exercises).toHaveLength(0)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })
})
