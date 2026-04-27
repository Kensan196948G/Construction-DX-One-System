<template>
  <div class="dashboard">
    <h2>BCP/ITSCM ダッシュボード</h2>

    <p v-if="loading">読み込み中...</p>
    <p v-else-if="errorMsg" class="error">{{ errorMsg }}</p>

    <div v-else class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-value incident-open">{{ incidentSummary?.total ?? '—' }}</div>
        <div class="kpi-label">アクティブ インシデント</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value incident-critical">{{ incidentSummary?.critical ?? '—' }}</div>
        <div class="kpi-label">クリティカル インシデント</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value bcp-active">{{ incidentSummary?.bcpActivated ?? '—' }}</div>
        <div class="kpi-label">BCP 発動中</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value rto-breach">{{ rtoOverview?.systemsBreachingRto ?? '—' }}</div>
        <div class="kpi-label">RTO 超過 システム</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value rto-total">{{ rtoOverview?.totalSystems ?? '—' }}</div>
        <div class="kpi-label">管理 IT システム数</div>
      </div>
    </div>

    <div v-if="rtoOverview" class="rto-summary">
      <h3>RTO 達成状況</h3>
      <div class="rto-bar-wrap">
        <div
          class="rto-bar-fill"
          :style="{ width: rtoPercent + '%' }"
          :title="`RTO 達成率: ${rtoPercent}%`"
        ></div>
      </div>
      <p class="rto-label">{{ rtoOverview.systemsMeetingRto }} / {{ rtoOverview.totalSystems }} システムが RTO 達成（{{ rtoPercent }}%）</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import type { DashboardRtoOverview, DashboardActiveIncidents } from '@/types'

const loading = ref(false)
const errorMsg = ref<string | null>(null)
const rtoOverview = ref<DashboardRtoOverview | null>(null)
const incidentSummary = ref<DashboardActiveIncidents | null>(null)

const rtoPercent = computed(() => {
  if (!rtoOverview.value || rtoOverview.value.totalSystems === 0) return 0
  return Math.round((rtoOverview.value.systemsMeetingRto / rtoOverview.value.totalSystems) * 100)
})

onMounted(async () => {
  loading.value = true
  try {
    const [rto, incidents] = await Promise.all([
      dashboardApi.rtoOverview(),
      dashboardApi.activeIncidentsSummary(),
    ])
    rtoOverview.value = rto
    incidentSummary.value = incidents
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : 'データ取得に失敗しました'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard { padding: 1rem; }
.kpi-grid { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.kpi-card {
  background: #1e1e2e; border: 1px solid #333; border-radius: 8px;
  padding: 1.25rem 2rem; text-align: center; min-width: 160px;
}
.kpi-value { font-size: 2.5rem; font-weight: bold; color: #cdd6f4; }
.kpi-value.incident-open { color: #fab387; }
.kpi-value.incident-critical { color: #f38ba8; }
.kpi-value.bcp-active { color: #cba6f7; }
.kpi-value.rto-breach { color: #f38ba8; }
.kpi-value.rto-total { color: #89b4fa; }
.kpi-label { font-size: 0.85rem; color: #a6adc8; margin-top: 0.25rem; }
.rto-summary { background: #1e1e2e; border: 1px solid #333; border-radius: 8px; padding: 1rem 1.5rem; max-width: 500px; }
.rto-summary h3 { margin-bottom: 0.75rem; font-size: 1rem; color: #a6adc8; }
.rto-bar-wrap { background: #313244; border-radius: 4px; height: 16px; overflow: hidden; margin-bottom: 0.5rem; }
.rto-bar-fill { background: #a6e3a1; height: 100%; transition: width 0.5s ease; }
.rto-label { font-size: 0.85rem; color: #a6adc8; }
.error { color: #f38ba8; }
</style>
