<template>
  <div class="dashboard">
    <h2>ダッシュボード</h2>
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-value rfc-pending">{{ pendingCount }}</div>
        <div class="kpi-label">承認待ち RFC</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value rfc-progress">{{ inProgressCount }}</div>
        <div class="kpi-label">実施中変更</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value">{{ rfcStore.rfcs.length }}</div>
        <div class="kpi-label">総 RFC 数</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value rfc-highrisk">{{ highRiskCount }}</div>
        <div class="kpi-label">高リスク RFC</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value cab-scheduled">{{ scheduledCabCount }}</div>
        <div class="kpi-label">予定 CAB 会議</div>
      </div>
    </div>

    <h3>最近の RFC</h3>
    <p v-if="rfcStore.loading">読み込み中...</p>
    <p v-else-if="rfcStore.error" class="error">{{ rfcStore.error }}</p>
    <table v-else-if="rfcStore.rfcs.length" class="data-table">
      <thead>
        <tr>
          <th>RFC番号</th>
          <th>タイトル</th>
          <th>種別</th>
          <th>優先度</th>
          <th>ステータス</th>
          <th>リスクスコア</th>
          <th>計画開始</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rfc in recentRfcs" :key="rfc.id">
          <td><code>{{ rfc.rfcNumber }}</code></td>
          <td>{{ rfc.title }}</td>
          <td><span :class="['badge', 'type-' + rfc.changeType]">{{ rfc.changeType }}</span></td>
          <td><span :class="['badge', 'priority-' + rfc.priority]">{{ rfc.priority }}</span></td>
          <td><span :class="['badge', 'status-' + rfc.status]">{{ rfc.status }}</span></td>
          <td :class="rfc.riskScore >= 15 ? 'high-score' : ''">{{ rfc.riskScore }}</td>
          <td>{{ formatDate(rfc.plannedStart) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>RFC はありません。</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRfcsStore } from '@/stores/rfcs'
import { useCabMeetingsStore } from '@/stores/cabMeetings'

const rfcStore = useRfcsStore()
const cabStore = useCabMeetingsStore()

onMounted(() => {
  rfcStore.fetchRfcs()
  cabStore.fetchMeetings()
})

const pendingCount = computed(() => rfcStore.pendingRfcs().length)
const inProgressCount = computed(() => rfcStore.inProgressRfcs().length)
const highRiskCount = computed(() => rfcStore.highRiskRfcs().length)
const scheduledCabCount = computed(() => cabStore.scheduledMeetings().length)
const recentRfcs = computed(() => rfcStore.rfcs.slice(0, 10))

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}
</script>

<style scoped>
.dashboard { padding: 1rem; }
.kpi-grid { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.kpi-card {
  background: #1e1e2e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 1.25rem 2rem;
  text-align: center;
  min-width: 160px;
}
.kpi-value { font-size: 2.5rem; font-weight: bold; color: #cdd6f4; }
.kpi-value.rfc-pending { color: #fab387; }
.kpi-value.rfc-progress { color: #89b4fa; }
.kpi-value.rfc-highrisk { color: #f38ba8; }
.kpi-value.cab-scheduled { color: #a6e3a1; }
.kpi-label { font-size: 0.85rem; color: #a6adc8; margin-top: 0.25rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.type-normal { background: #89b4fa; color: #1e1e2e; }
.type-emergency { background: #f38ba8; color: #1e1e2e; }
.type-standard { background: #a6e3a1; color: #1e1e2e; }
.priority-low { background: #6c7086; color: #cdd6f4; }
.priority-medium { background: #f9e2af; color: #1e1e2e; }
.priority-high { background: #fab387; color: #1e1e2e; }
.priority-critical { background: #f38ba8; color: #1e1e2e; }
.status-draft { background: #45475a; color: #cdd6f4; }
.status-pending_approval { background: #fab387; color: #1e1e2e; }
.status-cab_review { background: #cba6f7; color: #1e1e2e; }
.status-approved { background: #a6e3a1; color: #1e1e2e; }
.status-rejected { background: #f38ba8; color: #1e1e2e; }
.status-in_progress { background: #89b4fa; color: #1e1e2e; }
.status-completed { background: #313244; color: #a6e3a1; }
.status-cancelled { background: #45475a; color: #a6adc8; }
.high-score { color: #f38ba8; font-weight: bold; }
.error { color: #f38ba8; }
</style>
