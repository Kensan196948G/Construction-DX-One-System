<template>
  <div class="kpi-view">
    <div class="header-row">
      <h2>KPI ダッシュボード</h2>
      <button @click="store.fetchKpi()" :disabled="store.loading">
        {{ store.loading ? '更新中...' : '更新' }}
      </button>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>

    <div v-else-if="store.kpiData" class="kpi-grid">
      <!-- 変更成功率 -->
      <div class="kpi-card">
        <div class="kpi-icon">✅</div>
        <div class="kpi-label">変更成功率</div>
        <div class="kpi-value" :class="successRateClass">
          {{ formatPercent(store.kpiData.change_success_rate) }}
        </div>
      </div>

      <!-- 総変更件数 -->
      <div class="kpi-card">
        <div class="kpi-icon">📋</div>
        <div class="kpi-label">総変更件数</div>
        <div class="kpi-value">
          {{ formatCount(store.kpiData.total_changes) }}
        </div>
      </div>

      <!-- 成功変更数 -->
      <div class="kpi-card">
        <div class="kpi-icon">🟢</div>
        <div class="kpi-label">成功変更数</div>
        <div class="kpi-value kpi-success">
          {{ formatCount(store.kpiData.successful_changes) }}
        </div>
      </div>

      <!-- 失敗変更数 -->
      <div class="kpi-card">
        <div class="kpi-icon">🔴</div>
        <div class="kpi-label">失敗変更数</div>
        <div class="kpi-value kpi-danger">
          {{ formatCount(store.kpiData.failed_changes) }}
        </div>
      </div>

      <!-- 平均リードタイム -->
      <div class="kpi-card">
        <div class="kpi-icon">⏱️</div>
        <div class="kpi-label">平均リードタイム</div>
        <div class="kpi-value">
          {{ formatDays(store.kpiData.avg_lead_time_days) }}
        </div>
      </div>

      <!-- 承認待ち件数 -->
      <div class="kpi-card">
        <div class="kpi-icon">⏳</div>
        <div class="kpi-label">承認待ち件数</div>
        <div class="kpi-value" :class="store.kpiData.pending_approvals ? 'kpi-warning' : ''">
          {{ formatCount(store.kpiData.pending_approvals) }}
        </div>
      </div>

      <!-- オープンRFC数 -->
      <div class="kpi-card">
        <div class="kpi-icon">📝</div>
        <div class="kpi-label">オープン RFC 数</div>
        <div class="kpi-value">
          {{ formatCount(store.kpiData.open_rfcs) }}
        </div>
      </div>

      <!-- 緊急変更数 -->
      <div class="kpi-card">
        <div class="kpi-icon">🚨</div>
        <div class="kpi-label">緊急変更数</div>
        <div class="kpi-value" :class="store.kpiData.emergency_changes ? 'kpi-danger' : ''">
          {{ formatCount(store.kpiData.emergency_changes) }}
        </div>
      </div>

      <!-- 今月のCAB会議数 -->
      <div class="kpi-card">
        <div class="kpi-icon">🏛️</div>
        <div class="kpi-label">今月の CAB 会議数</div>
        <div class="kpi-value">
          {{ formatCount(store.kpiData.cab_meetings_this_month) }}
        </div>
      </div>
    </div>

    <p v-else class="no-data">データがありません。「更新」ボタンを押してください。</p>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useKpiStore } from '@/stores/kpi'

const store = useKpiStore()

onMounted(() => store.fetchKpi())

const successRateClass = computed(() => {
  const rate = store.kpiData?.change_success_rate
  if (rate == null) return ''
  if (rate >= 0.95) return 'kpi-success'
  if (rate >= 0.8) return 'kpi-warning'
  return 'kpi-danger'
})

function formatPercent(value: number | null | undefined): string {
  if (value == null) return '—'
  return `${(value * 100).toFixed(1)}%`
}

function formatCount(value: number | null | undefined): string {
  if (value == null) return '—'
  return value.toLocaleString('ja-JP')
}

function formatDays(value: number | null | undefined): string {
  if (value == null) return '—'
  return `${value.toFixed(1)} 日`
}
</script>

<style scoped>
.kpi-view { padding: 1rem; }
.header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; }
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
.kpi-card {
  background: #1e1e2e;
  border: 1px solid #313244;
  border-radius: 8px;
  padding: 1.25rem 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  text-align: center;
}
.kpi-icon { font-size: 1.75rem; }
.kpi-label { font-size: 0.8rem; color: #a6adc8; }
.kpi-value { font-size: 1.8rem; font-weight: 700; color: #cdd6f4; line-height: 1.2; }
.kpi-success { color: #a6e3a1; }
.kpi-warning { color: #f9e2af; }
.kpi-danger { color: #f38ba8; }
.error { color: #f38ba8; font-size: 0.9rem; }
.no-data { color: #6c7086; font-size: 0.9rem; margin-top: 1rem; }
</style>
