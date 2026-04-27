import client from './client'
import type { Exercise, ExerciseStatus, ExerciseType } from '@/types'

interface ListResponse<T> {
  data: T[]
  pagination: { total_count: number; has_next: boolean }
}

export const exercisesApi = {
  list(status?: ExerciseStatus, type?: ExerciseType, limit = 30): Promise<Exercise[]> {
    return client
      .get<ListResponse<Exercise>>('/exercises', { params: { status, type, limit } })
      .then((r) => r.data.data)
  },
}
