import { ref } from 'vue'
import { defineStore } from 'pinia'
import { exercisesApi } from '@/api/exercises'
import type { Exercise, ExerciseStatus, ExerciseType } from '@/types'

export const useExercisesStore = defineStore('exercises', () => {
  const exercises = ref<Exercise[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const plannedExercises = () => exercises.value.filter((e) => e.status === 'planned')
  const completedExercises = () => exercises.value.filter((e) => e.status === 'completed')
  const inProgressExercises = () => exercises.value.filter((e) => e.status === 'in_progress')

  async function fetchExercises(status?: ExerciseStatus, type?: ExerciseType) {
    loading.value = true
    error.value = null
    try {
      exercises.value = await exercisesApi.list(status, type)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'データ取得に失敗しました'
    } finally {
      loading.value = false
    }
  }

  return { exercises, loading, error, plannedExercises, completedExercises, inProgressExercises, fetchExercises }
})
