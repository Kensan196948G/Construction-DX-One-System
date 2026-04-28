<template>
  <div class="integration-hub">
    <h2>統合ハブ <span class="subtitle">SIEM ↔ ZTIG / CAB</span></h2>

    <p v-if="store.error" class="error">{{ store.error }}</p>

    <!-- Alert Summary for CAB -->
    <section class="section">
      <h3>CAB向けアラートサマリー</h3>
      <p v-if="store.loading && !store.alertSummary" class="loading">読み込み中...</p>
      <div v-else-if="store.alertSummary" class="kpi-grid">
        <div class="kpi-card kpi-open">
          <div class="kpi-value">{{ store.alertSummary.total_open }}</div>
          <div class="kpi-label">オープン合計</div>
        </div>
        <div class="kpi-card kpi-critical">
          <div class="kpi-value">{{ store.alertSummary.critical_count }}</div>
          <div class="kpi-label">Critical</div>
        </div>
        <div class="kpi-card kpi-high">
          <div class="kpi-value">{{ store.alertSummary.high_count }}</div>
          <div class="kpi-label">High</div>
        </div>
        <div class="kpi-card kpi-medium">
          <div class="kpi-value">{{ store.alertSummary.medium_count }}</div>
          <div class="kpi-label">Medium</div>
        </div>
        <div class="kpi-card kpi-low">
          <div class="kpi-value">{{ store.alertSummary.low_count }}</div>
          <div class="kpi-label">Low</div>
        </div>
      </div>
      <p v-if="store.alertSummary" class="updated-at">最終更新: {{ formatDate(store.alertSummary.generated_at) }}</p>
    </section>

    <!-- Pending Incidents for CAB Escalation -->
    <section class="section">
      <div class="section-header">
        <h3>CABエスカレーション待ちインシデント</h3>
        <button class="refresh-btn" @click="store.fetchPendingIncidents()" :disabled="store.loading">
          更新
        </button>
      </div>
      <p v-if="store.loading && !store.pendingIncidents.length" class="loading">読み込み中...</p>
      <p v-else-if="!store.pendingIncidents.length" class="empty">エスカレーション待ちインシデントはありません。</p>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>タイトル</th>
            <th>重大度</th>
            <th>ステータス</th>
            <th>検知時刻</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inc in store.pendingIncidents" :key="inc.id">
            <td>{{ inc.title }}</td>
            <td><span :class="['badge', 'sev-' + inc.severity]">{{ inc.severity }}</span></td>
            <td><span :class="['badge', 'status-' + inc.status]">{{ inc.status }}</span></td>
            <td>{{ formatDate(inc.detected_at) }}</td>
            <td>
              <button
                class="escalate-btn"
                @click="handleEscalate(inc.id)"
                :disabled="store.loading"
              >
                CABへ送付
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Escalation Result -->
    <div v-if="store.escalateResult" class="toast-success">
      RFC起票完了: {{ store.escalateResult }}
    </div>

    <!-- Integration Map -->
    <section class="section">
      <h3>統合フロー</h3>
      <div class="flow-diagram">
        <div class="flow-node node-ztig">🔐 ZTIG<br><small>認証イベント</small></div>
        <div class="flow-arrow">→</div>
        <div class="flow-node node-siem node-current">🛡️ SIEM<br><small>アラート分析</small></div>
        <div class="flow-arrow">→</div>
        <div class="flow-node node-cab">📋 CAB<br><small>RFC管理</small></div>
        <div class="flow-arrow">→</div>
        <div class="flow-node node-bcp">🔄 BCP<br><small>事業継続</small></div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useIntegrationStore } from '@/stores/integration'

const store = useIntegrationStore()

onMounted(async () => {
  await Promise.all([store.fetchAlertSummary(), store.fetchPendingIncidents()])
})

async function handleEscalate(incidentId: string) {
  await store.escalate(incidentId, 'SIEM-Admin', 'High-severity incident requires CAB review')
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}
</script>

<style scoped>
.integration-hub { padding: 1rem; }
.subtitle { font-size: 0.85rem; color: #a6adc8; font-weight: normal; margin-left: 0.5rem; }
.section { margin-bottom: 2rem; }
.section-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem; }
.section-header h3 { margin: 0; }
h3 { margin-bottom: 0.75rem; color: #a6adc8; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-grid { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.kpi-card {
  background: #1e1e2e; border: 1px solid #313244; border-radius: 8px;
  padding: 1rem 1.5rem; text-align: center; min-width: 120px;
}
.kpi-value { font-size: 2rem; font-weight: bold; }
.kpi-label { font-size: 0.8rem; color: #a6adc8; margin-top: 0.2rem; }
.kpi-open .kpi-value { color: #cdd6f4; }
.kpi-critical .kpi-value { color: #f38ba8; }
.kpi-high .kpi-value { color: #fab387; }
.kpi-medium .kpi-value { color: #f9e2af; }
.kpi-low .kpi-value { color: #a6e3a1; }
.updated-at { font-size: 0.75rem; color: #585b70; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #313244; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.sev-critical { background: #f38ba8; color: #1e1e2e; }
.sev-high { background: #fab387; color: #1e1e2e; }
.sev-medium { background: #f9e2af; color: #1e1e2e; }
.sev-low { background: #a6e3a1; color: #1e1e2e; }
.status-open { background: #f38ba8; color: #1e1e2e; }
.status-investigating { background: #fab387; color: #1e1e2e; }
.status-escalated_to_cab { background: #89b4fa; color: #1e1e2e; }
.escalate-btn { font-size: 0.8rem; padding: 0.25rem 0.6rem; background: #89b4fa; color: #1e1e2e; border: none; border-radius: 4px; cursor: pointer; }
.escalate-btn:hover { background: #74c7ec; }
.escalate-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.refresh-btn { font-size: 0.8rem; padding: 0.25rem 0.6rem; }
.loading { color: #a6adc8; }
.empty { color: #585b70; font-size: 0.9rem; }
.error { color: #f38ba8; margin-bottom: 1rem; }
.toast-success {
  background: #1e4a2e; border: 1px solid #a6e3a1; color: #a6e3a1;
  padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1.5rem; font-size: 0.9rem;
}
.flow-diagram {
  display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;
  background: #1e1e2e; padding: 1.5rem; border-radius: 8px; border: 1px solid #313244;
}
.flow-node {
  padding: 0.75rem 1.25rem; border-radius: 8px; text-align: center; font-size: 0.9rem;
  border: 1px solid #45475a; min-width: 100px; line-height: 1.4;
}
.flow-node small { font-size: 0.7rem; color: #a6adc8; }
.node-ztig { background: #2a2a3e; border-color: #89b4fa; }
.node-siem { background: #1e1e2e; }
.node-current { border-color: #cba6f7; box-shadow: 0 0 8px #cba6f740; }
.node-cab { background: #2a3e2a; border-color: #a6e3a1; }
.node-bcp { background: #3e2a2a; border-color: #fab387; }
.flow-arrow { color: #585b70; font-size: 1.5rem; }
</style>
