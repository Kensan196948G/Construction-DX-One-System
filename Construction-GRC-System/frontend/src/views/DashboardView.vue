<template>
  <div class="dashboard">
    <h1>GRC ダッシュボード</h1>

    <div v-if="loadingAll" class="loading">読み込み中...</div>
    <div v-else-if="errorMsg" class="error">{{ errorMsg }}</div>

    <div v-else class="kpi-grid">
      <div class="kpi-card risk">
        <div class="kpi-label">オープンリスク</div>
        <div class="kpi-value">{{ openRisksCount }}</div>
        <div class="kpi-sub">高リスク: {{ highRisksCount }}</div>
      </div>

      <div class="kpi-card control">
        <div class="kpi-label">管理策（未対応）</div>
        <div class="kpi-value">{{ notStartedControlsCount }}</div>
        <div class="kpi-sub">全管理策: {{ controlsTotal }}</div>
      </div>

      <div class="kpi-card audit">
        <div class="kpi-label">進行中の監査</div>
        <div class="kpi-value">{{ inProgressAuditsCount }}</div>
        <div class="kpi-sub">計画済み: {{ plannedAuditsCount }}</div>
      </div>

      <div class="kpi-card finding">
        <div class="kpi-label">未解決の指摘</div>
        <div class="kpi-value">{{ openFindingsCount }}</div>
      </div>
    </div>

    <div class="quick-links">
      <router-link to="/risks">→ リスク管理</router-link>
      <router-link to="/compliance">→ コンプライアンス</router-link>
      <router-link to="/audits">→ 監査管理</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { risksApi } from '@/api/risks'
import { complianceApi } from '@/api/compliance'
import { auditsApi } from '@/api/audits'
import type { Risk, Control, Audit } from '@/types'

const risks = ref<Risk[]>([])
const controls = ref<Control[]>([])
const audits = ref<Audit[]>([])
const loadingAll = ref(true)
const errorMsg = ref<string | null>(null)

const openRisksCount = computed(() => risks.value.filter((r) => r.status === 'open').length)
const highRisksCount = computed(() => risks.value.filter((r) => r.risk_score >= 15).length)
const controlsTotal = computed(() => controls.value.length)
const notStartedControlsCount = computed(
  () => controls.value.filter((c) => c.implementation_status === 'not_started').length,
)
const inProgressAuditsCount = computed(
  () => audits.value.filter((a) => a.status === 'in_progress').length,
)
const plannedAuditsCount = computed(
  () => audits.value.filter((a) => a.status === 'planned').length,
)
const openFindingsCount = computed(() =>
  audits.value.reduce((sum, a) => sum + a.findings.filter((f) => f.status === 'open').length, 0),
)

onMounted(async () => {
  try {
    const [r, c, a] = await Promise.all([risksApi.list(), complianceApi.list(), auditsApi.list()])
    risks.value = r
    controls.value = c
    audits.value = a
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : 'データの取得に失敗しました'
  } finally {
    loadingAll.value = false
  }
})
</script>

<style scoped>
.dashboard { padding: 1.5rem; }
h1 { margin-bottom: 1.5rem; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
.kpi-card { padding: 1.25rem; border-radius: 8px; background: #f5f5f5; }
.kpi-card.risk { border-left: 4px solid #e53935; }
.kpi-card.control { border-left: 4px solid #1565c0; }
.kpi-card.audit { border-left: 4px solid #2e7d32; }
.kpi-card.finding { border-left: 4px solid #f57f17; }
.kpi-label { font-size: 0.85rem; color: #666; }
.kpi-value { font-size: 2.5rem; font-weight: bold; }
.kpi-sub { font-size: 0.8rem; color: #888; }
.quick-links { margin-top: 2rem; display: flex; gap: 1rem; }
.quick-links a { color: #1565c0; text-decoration: none; }
.loading, .error { padding: 1rem; }
.error { color: #e53935; }
</style>
