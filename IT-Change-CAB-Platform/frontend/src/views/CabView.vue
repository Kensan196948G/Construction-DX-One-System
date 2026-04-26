<template>
  <div class="cab-view">
    <h2>CAB 会議</h2>

    <div class="filter-bar">
      <select v-model="filterStatus" @change="applyFilter">
        <option value="">全ステータス</option>
        <option value="scheduled">予定</option>
        <option value="in_progress">進行中</option>
        <option value="completed">完了</option>
        <option value="cancelled">キャンセル</option>
      </select>
    </div>

    <p v-if="cabStore.loading">読み込み中...</p>
    <p v-else-if="cabStore.error" class="error">{{ cabStore.error }}</p>
    <table v-else-if="cabStore.meetings.length" class="data-table">
      <thead>
        <tr>
          <th>会議番号</th>
          <th>タイトル</th>
          <th>ステータス</th>
          <th>予定日時</th>
          <th>ファシリテーター</th>
          <th>RFC 件数</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in cabStore.meetings" :key="m.id">
          <td><code>{{ m.meetingNumber }}</code></td>
          <td>{{ m.title }}</td>
          <td><span :class="['badge', 'cab-' + m.status]">{{ cabStatusLabel(m.status) }}</span></td>
          <td>{{ formatDate(m.scheduledAt) }}</td>
          <td>{{ m.facilitator ?? '—' }}</td>
          <td>{{ m.rfcCount }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>CAB 会議はありません。</p>

    <div class="summary-row">
      <div class="summary-card">
        <div class="summary-value">{{ cabStore.scheduledMeetings().length }}</div>
        <div class="summary-label">予定会議数</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ cabStore.completedMeetings().length }}</div>
        <div class="summary-label">完了会議数</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCabMeetingsStore } from '@/stores/cabMeetings'
import type { CabStatus } from '@/types'

const cabStore = useCabMeetingsStore()
const filterStatus = ref<CabStatus | ''>('')

onMounted(() => cabStore.fetchMeetings())

function applyFilter() {
  cabStore.fetchMeetings(filterStatus.value || undefined)
}

function cabStatusLabel(v: CabStatus): string {
  return { scheduled: '予定', in_progress: '進行中', completed: '完了', cancelled: 'キャンセル' }[v] ?? v
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}
</script>

<style scoped>
.cab-view { padding: 1rem; }
.filter-bar { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-bottom: 1.5rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.cab-scheduled { background: #a6e3a1; color: #1e1e2e; }
.cab-in_progress { background: #89b4fa; color: #1e1e2e; }
.cab-completed { background: #313244; color: #a6e3a1; }
.cab-cancelled { background: #45475a; color: #a6adc8; }
.summary-row { display: flex; gap: 1rem; }
.summary-card { background: #1e1e2e; border: 1px solid #333; border-radius: 8px; padding: 1rem 1.5rem; text-align: center; min-width: 140px; }
.summary-value { font-size: 2rem; font-weight: bold; color: #cdd6f4; }
.summary-label { font-size: 0.8rem; color: #a6adc8; margin-top: 0.25rem; }
.error { color: #f38ba8; }
</style>
