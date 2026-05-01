<template>
  <div class="integration-view">
    <h2>統合ステータス <span class="subtitle">ZTIG → SIEM</span></h2>

    <p v-if="store.error" class="error">{{ store.error }}</p>

    <!-- Identity Summary -->
    <section class="section">
      <h3>ID サマリー（SIEM連携用）</h3>
      <p v-if="store.loading && !store.identitySummary" class="loading">読み込み中...</p>
      <div v-else-if="store.identitySummary" class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-value">{{ store.identitySummary.total_users }}</div>
          <div class="kpi-label">総ユーザー数</div>
        </div>
        <div class="kpi-card kpi-active">
          <div class="kpi-value">{{ store.identitySummary.active_users }}</div>
          <div class="kpi-label">アクティブ</div>
        </div>
        <div class="kpi-card kpi-priv">
          <div class="kpi-value">{{ store.identitySummary.privileged_users }}</div>
          <div class="kpi-label">特権ユーザー</div>
        </div>
      </div>
      <p v-if="store.identitySummary" class="updated-at">最終更新: {{ formatDate(store.identitySummary.generated_at) }}</p>
    </section>

    <!-- Auth Events -->
    <section class="section">
      <div class="section-header">
        <h3>最近の認証イベント（SIEM転送対象）</h3>
        <div class="period-selector">
          期間:
          <select v-model="selectedHours" @change="loadEvents">
            <option value="1">直近1時間</option>
            <option value="6">直近6時間</option>
            <option value="24">直近24時間</option>
          </select>
        </div>
        <button class="refresh-btn" @click="loadEvents" :disabled="store.loading">更新</button>
      </div>
      <p v-if="store.loading" class="loading">読み込み中...</p>
      <template v-else-if="store.authEvents">
        <p class="count-label">
          {{ store.authEvents.period_hours }}時間以内: {{ store.authEvents.total_count }}件
        </p>
        <p v-if="!store.authEvents.events.length" class="empty">認証イベントはありません。</p>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>タイプ</th>
              <th>ユーザー名</th>
              <th>IPアドレス</th>
              <th>重大度</th>
              <th>タイムスタンプ</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ev in store.authEvents.events" :key="ev.id">
              <td><span class="event-type">{{ ev.event_type }}</span></td>
              <td>{{ ev.username }}</td>
              <td class="ip">{{ ev.actor_ip }}</td>
              <td><span :class="['badge', 'sev-' + ev.severity]">{{ ev.severity }}</span></td>
              <td>{{ formatDate(ev.timestamp) }}</td>
            </tr>
          </tbody>
        </table>
      </template>
    </section>

    <!-- Integration Flow -->
    <section class="section">
      <h3>統合フロー</h3>
      <div class="flow-diagram">
        <div class="flow-node node-current">🔐 ZTIG<br><small>ID・認証管理</small></div>
        <div class="flow-arrow">→</div>
        <div class="flow-node node-siem">🛡️ SIEM<br><small>セキュリティ分析</small></div>
        <div class="flow-divider">|</div>
        <div class="flow-node node-grc">📊 GRC<br><small>リスク管理</small></div>
      </div>
      <div class="legend">
        <span class="legend-item">🔑 認証イベント → SIEM転送</span>
        <span class="legend-item">👥 IDサマリー → GRC提供</span>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useIntegrationStore } from '@/stores/integration'

const store = useIntegrationStore()
const selectedHours = ref<number>(1)

onMounted(async () => {
  await Promise.all([store.fetchIdentitySummary(), store.fetchAuthEvents(1)])
})

async function loadEvents() {
  await store.fetchAuthEvents(Number(selectedHours.value))
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}
</script>

<style scoped>
.integration-view { padding: 1rem; }
.subtitle { font-size: 0.85rem; color: #a6adc8; font-weight: normal; margin-left: 0.5rem; }
.section { margin-bottom: 2rem; }
.section-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.section-header h3 { margin: 0; }
h3 { margin-bottom: 0.75rem; color: #a6adc8; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-grid { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.kpi-card {
  background: #1e1e2e; border: 1px solid #313244; border-radius: 8px;
  padding: 1rem 1.5rem; text-align: center; min-width: 130px;
}
.kpi-value { font-size: 2rem; font-weight: bold; color: #cdd6f4; }
.kpi-label { font-size: 0.8rem; color: #a6adc8; margin-top: 0.2rem; }
.kpi-active .kpi-value { color: #a6e3a1; }
.kpi-priv .kpi-value { color: #fab387; }
.updated-at { font-size: 0.75rem; color: #585b70; }
.count-label { font-size: 0.85rem; color: #a6adc8; margin-bottom: 0.5rem; }
.period-selector { display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; color: #a6adc8; }
.refresh-btn { font-size: 0.8rem; padding: 0.25rem 0.6rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #313244; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.event-type { font-family: monospace; font-size: 0.85rem; color: #89b4fa; }
.ip { font-family: monospace; font-size: 0.85rem; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.sev-critical { background: #f38ba8; color: #1e1e2e; }
.sev-high { background: #fab387; color: #1e1e2e; }
.sev-medium { background: #f9e2af; color: #1e1e2e; }
.sev-low { background: #a6e3a1; color: #1e1e2e; }
.loading { color: #a6adc8; }
.empty { color: #585b70; font-size: 0.9rem; }
.error { color: #f38ba8; margin-bottom: 1rem; }
.flow-diagram {
  display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;
  background: #1e1e2e; padding: 1.5rem; border-radius: 8px; border: 1px solid #313244;
}
.flow-node {
  padding: 0.75rem 1.25rem; border-radius: 8px; text-align: center; font-size: 0.9rem;
  border: 1px solid #45475a; min-width: 100px; line-height: 1.4;
}
.flow-node small { font-size: 0.7rem; color: #a6adc8; }
.node-current { background: #1e1e2e; border-color: #89b4fa; box-shadow: 0 0 8px #89b4fa40; }
.node-siem { background: #2a2a3e; border-color: #cba6f7; }
.node-grc { background: #2a3e3e; border-color: #94e2d5; }
.flow-arrow { color: #585b70; font-size: 1.5rem; }
.flow-divider { color: #585b70; font-size: 1.5rem; margin: 0 0.25rem; }
.legend { display: flex; gap: 1.5rem; margin-top: 1rem; flex-wrap: wrap; }
.legend-item { font-size: 0.8rem; color: #a6adc8; }
</style>
