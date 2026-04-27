<template>
  <div class="dashboard">
    <h2>ダッシュボード</h2>
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-value alert-open">{{ openCount }}</div>
        <div class="kpi-label">オープンアラート</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value alert-critical">{{ criticalCount }}</div>
        <div class="kpi-label">高重大度アラート</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value">{{ store.alerts.length }}</div>
        <div class="kpi-label">総アラート数</div>
      </div>
    </div>

    <h3>最近のアラート</h3>
    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>
    <table v-else-if="store.alerts.length" class="data-table">
      <thead>
        <tr>
          <th>タイトル</th>
          <th>重大度</th>
          <th>ステータス</th>
          <th>検知時刻</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="alert in recentAlerts" :key="alert.id">
          <td>{{ alert.title }}</td>
          <td><span :class="['badge', 'sev-' + alert.severity]">{{ alert.severity }}</span></td>
          <td><span :class="['badge', 'status-' + alert.status]">{{ alert.status }}</span></td>
          <td>{{ formatDate(alert.detected_at) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>アラートはありません。</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useAlertsStore } from '@/stores/alerts'

const store = useAlertsStore()

onMounted(() => store.fetchAlerts())

const openCount = computed(() => store.openAlerts().length)
const criticalCount = computed(() => store.criticalAlerts().length)
const recentAlerts = computed(() => store.alerts.slice(0, 10))

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
.kpi-value.alert-open { color: #f38ba8; }
.kpi-value.alert-critical { color: #fab387; }
.kpi-label { font-size: 0.85rem; color: #a6adc8; margin-top: 0.25rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.sev-critical { background: #f38ba8; color: #1e1e2e; }
.sev-high { background: #fab387; color: #1e1e2e; }
.sev-medium { background: #f9e2af; color: #1e1e2e; }
.sev-low { background: #a6e3a1; color: #1e1e2e; }
.sev-info { background: #89b4fa; color: #1e1e2e; }
.status-open { background: #f38ba8; color: #1e1e2e; }
.status-investigating { background: #fab387; color: #1e1e2e; }
.status-resolved { background: #a6e3a1; color: #1e1e2e; }
.status-false_positive { background: #6c7086; color: #cdd6f4; }
.error { color: #f38ba8; }
</style>
