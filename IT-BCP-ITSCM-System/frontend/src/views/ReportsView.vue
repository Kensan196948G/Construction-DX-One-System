<template>
  <div class="reports">
    <div class="page-header">
      <h2>レポート・経営報告</h2>
    </div>

    <p v-if="store.error" class="error">{{ store.error }}</p>

    <!-- Executive Summary -->
    <section class="report-section">
      <div class="section-header">
        <h3>エグゼクティブサマリー</h3>
        <button @click="loadExecutiveSummary" :disabled="store.loading">
          {{ store.loading ? '取得中...' : '更新' }}
        </button>
      </div>

      <div v-if="store.executiveSummary" class="cards-grid">
        <div class="card">
          <div class="card-label">総インシデント数</div>
          <div class="card-value">{{ store.executiveSummary.total_incidents ?? store.executiveSummary.totalIncidents ?? '—' }}</div>
        </div>
        <div class="card">
          <div class="card-label">重大インシデント数</div>
          <div class="card-value critical">{{ store.executiveSummary.critical_incidents ?? store.executiveSummary.criticalIncidents ?? '—' }}</div>
        </div>
        <div class="card">
          <div class="card-label">重大インシデント率</div>
          <div class="card-value">{{ formatPercent(store.executiveSummary.critical_rate ?? store.executiveSummary.criticalRate) }}</div>
        </div>
        <div class="card">
          <div class="card-label">BCP 発動回数</div>
          <div class="card-value">{{ store.executiveSummary.bcp_activations ?? store.executiveSummary.bcpActivations ?? '—' }}</div>
        </div>
        <div class="card">
          <div class="card-label">平均復旧時間 (時間)</div>
          <div class="card-value">{{ formatNum(store.executiveSummary.avg_recovery_hours ?? store.executiveSummary.avgRecoveryHours) }}</div>
        </div>
        <div class="card">
          <div class="card-label">未解決インシデント</div>
          <div class="card-value warn">{{ store.executiveSummary.open_incidents ?? store.executiveSummary.openIncidents ?? '—' }}</div>
        </div>
      </div>
      <div v-else class="empty-card">
        <p>「更新」ボタンを押してサマリーを取得してください。</p>
      </div>

      <div v-if="store.executiveSummary" class="raw-section">
        <details>
          <summary>JSON 詳細データ</summary>
          <pre>{{ JSON.stringify(store.executiveSummary, null, 2) }}</pre>
        </details>
      </div>
    </section>

    <!-- System Status Report -->
    <section class="report-section">
      <div class="section-header">
        <h3>システム状態レポート</h3>
        <button @click="loadSystemStatus" :disabled="store.loading">
          {{ store.loading ? '取得中...' : '更新' }}
        </button>
      </div>

      <div v-if="store.systemStatus" class="cards-grid">
        <div class="card">
          <div class="card-label">総システム数</div>
          <div class="card-value">{{ store.systemStatus.total_systems ?? store.systemStatus.totalSystems ?? '—' }}</div>
        </div>
        <div class="card">
          <div class="card-label">正常稼働中</div>
          <div class="card-value ok">{{ store.systemStatus.normal_systems ?? store.systemStatus.normalSystems ?? '—' }}</div>
        </div>
        <div class="card">
          <div class="card-label">劣化中</div>
          <div class="card-value warn">{{ store.systemStatus.degraded_systems ?? store.systemStatus.degradedSystems ?? '—' }}</div>
        </div>
        <div class="card">
          <div class="card-label">停止中</div>
          <div class="card-value critical">{{ store.systemStatus.down_systems ?? store.systemStatus.downSystems ?? '—' }}</div>
        </div>
        <div class="card">
          <div class="card-label">Tier 1 システム数</div>
          <div class="card-value">{{ store.systemStatus.tier1_count ?? store.systemStatus.tier1Count ?? '—' }}</div>
        </div>
        <div class="card">
          <div class="card-label">システム可用率</div>
          <div class="card-value">{{ formatPercent(store.systemStatus.availability_rate ?? store.systemStatus.availabilityRate) }}</div>
        </div>
      </div>
      <div v-else class="empty-card">
        <p>「更新」ボタンを押してシステム状態を取得してください。</p>
      </div>

      <div v-if="store.systemStatus" class="raw-section">
        <details>
          <summary>JSON 詳細データ</summary>
          <pre>{{ JSON.stringify(store.systemStatus, null, 2) }}</pre>
        </details>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useReportsStore } from '@/stores/reports'

const store = useReportsStore()

async function loadExecutiveSummary() {
  await store.fetchExecutiveSummary()
}

async function loadSystemStatus() {
  await store.fetchSystemStatus()
}

function formatPercent(val: number | undefined | null): string {
  if (val == null) return '—'
  return (val * 100).toFixed(1) + '%'
}

function formatNum(val: number | undefined | null): string {
  if (val == null) return '—'
  return val.toFixed(1)
}
</script>

<style scoped>
.reports { padding: 1rem; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.report-section { margin-bottom: 2rem; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid #313244; padding-bottom: 0.5rem; }
.section-header h3 { color: #cdd6f4; font-size: 1rem; }
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }
.card { background: #1e1e2e; border: 1px solid #313244; border-radius: 8px; padding: 1rem; }
.card-label { font-size: 0.78rem; color: #a6adc8; margin-bottom: 0.4rem; }
.card-value { font-size: 1.6rem; font-weight: 700; color: #cdd6f4; }
.card-value.critical { color: #f38ba8; }
.card-value.warn { color: #fab387; }
.card-value.ok { color: #a6e3a1; }
.empty-card { background: #1e1e2e; border: 1px solid #313244; border-radius: 8px; padding: 1.5rem; text-align: center; color: #6c7086; font-size: 0.9rem; margin-bottom: 1rem; }
.raw-section { margin-top: 0.5rem; }
.raw-section details { background: #1e1e2e; border: 1px solid #313244; border-radius: 4px; padding: 0.5rem 0.75rem; }
.raw-section summary { cursor: pointer; font-size: 0.82rem; color: #a6adc8; }
.raw-section pre { margin-top: 0.5rem; font-size: 0.78rem; color: #cdd6f4; overflow: auto; max-height: 200px; }
.error { color: #f38ba8; font-size: 0.85rem; margin-bottom: 1rem; }
</style>
