import { defineStore } from 'pinia'
import { ref } from 'vue'
import { eventsApi } from '@/api/events'
import type { SecurityEvent, SecurityEventCreate } from '@/types'

export interface EventStats {
  total: number
  by_severity: Record<string, number>
  processed: number
  unprocessed: number
}

export const useEventsStore = defineStore('events', () => {
  const events = ref<SecurityEvent[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const stats = ref<EventStats | null>(null)

  async function fetchEvents(limit = 50, offset = 0) {
    loading.value = true
    error.value = null
    try {
      events.value = await eventsApi.list(undefined, limit, offset)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load events'
    } finally {
      loading.value = false
    }
  }

  async function createEvent(data: SecurityEventCreate): Promise<SecurityEvent | null> {
    try {
      const event = await eventsApi.ingest(data)
      events.value.unshift(event)
      return event
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create event'
      return null
    }
  }

  async function fetchStats() {
    try {
      const all = await eventsApi.list(undefined, 1000, 0)
      const by_severity: Record<string, number> = {}
      let processed = 0
      for (const ev of all) {
        by_severity[ev.severity] = (by_severity[ev.severity] ?? 0) + 1
        if (ev.is_processed) processed++
      }
      stats.value = {
        total: all.length,
        by_severity,
        processed,
        unprocessed: all.length - processed,
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load stats'
    }
  }

  return {
    events,
    loading,
    error,
    stats,
    fetchEvents,
    createEvent,
    fetchStats,
  }
})
