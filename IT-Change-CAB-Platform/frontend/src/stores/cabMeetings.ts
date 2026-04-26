import { defineStore } from 'pinia'
import { ref } from 'vue'
import { cabMeetingsApi } from '@/api/cabMeetings'
import type { CabMeeting, CabStatus } from '@/types'

export const useCabMeetingsStore = defineStore('cabMeetings', () => {
  const meetings = ref<CabMeeting[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchMeetings(status?: CabStatus) {
    loading.value = true
    error.value = null
    try {
      meetings.value = await cabMeetingsApi.list(status)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load CAB meetings'
    } finally {
      loading.value = false
    }
  }

  const scheduledMeetings = () => meetings.value.filter((m) => m.status === 'scheduled')
  const completedMeetings = () => meetings.value.filter((m) => m.status === 'completed')

  return {
    meetings,
    loading,
    error,
    fetchMeetings,
    scheduledMeetings,
    completedMeetings,
  }
})
