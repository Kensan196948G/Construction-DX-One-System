<template>
  <div class="events-view">
    <h2>セキュリティイベント</h2>

    <div class="toolbar">
      <label>
        重大度フィルター:
        <select v-model="severityFilter" @change="loadEvents">
          <option value="">すべて</option>
          <option value="critical">critical</option>
          <option value="high">high</option>
          <option value="medium">medium</option>
          <option value="low">low</option>
          <option value="info">info</option>
        </select>
      </label>
      <button @click="loadEvents">更新</button>
    </div>

    <p v-if="loading">読み込み中...</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <table v-else-if="events.length" class="data-table">
      <thead>
        <tr>
          <th>種別</th>
          <th>重大度</th>
          <th>送信元 IP</th>
          <th>送信先 IP:Port</th>
          <th>リスクスコア</th>
          <th>発生時刻</th>
          <th>処理済</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ev in events" :key="ev.id">
          <td>{{ ev.event_type }}</td>
          <td><span :class="['badge', 'sev-' + ev.severity]">{{ ev.severity }}</span></td>
          <td>{{ ev.source_ip ?? '-' }}</td>
          <td>{{ ev.destination_ip ?? '-' }}{{ ev.destination_port ? ':' + ev.destination_port : '' }}</td>
          <td>{{ ev.risk_score }}</td>
          <td>{{ formatDate(ev.occurred_at) }}</td>
          <td>
            <span v-if="ev.is_processed" class="badge status-resolved">済</span>
            <button v-else @click="markProcessed(ev.id)" class="btn-small">処理済にする</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>イベントはありません。</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { eventsApi } from '@/api/events'
import type { SecurityEvent, EventSeverity } from '@/types'

const events = ref<SecurityEvent[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const severityFilter = ref<EventSeverity | ''>('')

async function loadEvents() {
  loading.value = true
  error.value = null
  try {
    events.value = await eventsApi.list(severityFilter.value || undefined)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load events'
  } finally {
    loading.value = false
  }
}

async function markProcessed(id: string) {
  try {
    const updated = await eventsApi.markProcessed(id)
    const idx = events.value.findIndex((e) => e.id === id)
    if (idx !== -1) events.value[idx] = updated
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to update event'
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}

onMounted(loadEvents)
</script>

<style scoped>
.events-view { padding: 1rem; }
.toolbar { display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.4rem 0.6rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.sev-critical { background: #f38ba8; color: #1e1e2e; }
.sev-high { background: #fab387; color: #1e1e2e; }
.sev-medium { background: #f9e2af; color: #1e1e2e; }
.sev-low { background: #a6e3a1; color: #1e1e2e; }
.sev-info { background: #89b4fa; color: #1e1e2e; }
.status-resolved { background: #a6e3a1; color: #1e1e2e; }
.btn-small { padding: 0.2rem 0.5rem; font-size: 0.75rem; cursor: pointer; }
.error { color: #f38ba8; }
</style>
