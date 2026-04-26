<template>
  <div class="systems">
    <h2>IT システム管理</h2>

    <div class="filters">
      <select v-model="filterTier" @change="applyFilter">
        <option value="">Tier: すべて</option>
        <option value="tier1">Tier 1（最重要）</option>
        <option value="tier2">Tier 2</option>
        <option value="tier3">Tier 3</option>
        <option value="tier4">Tier 4</option>
      </select>
      <select v-model="filterStatus" @change="applyFilter">
        <option value="">ステータス: すべて</option>
        <option value="normal">正常</option>
        <option value="degraded">劣化</option>
        <option value="down">停止</option>
        <option value="maintenance">メンテナンス</option>
      </select>
    </div>

    <div class="summary-row">
      <div class="summary-chip">Tier1: <strong>{{ store.tier1Systems().length }}</strong></div>
      <div class="summary-chip">障害/劣化: <strong>{{ store.degradedSystems().length }}</strong></div>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>

    <table v-else class="data-table">
      <thead>
        <tr>
          <th>システム名</th>
          <th>Tier</th>
          <th>ステータス</th>
          <th>RTO（分）</th>
          <th>RPO（分）</th>
          <th>優先度</th>
          <th>オーナー</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="sys in store.systems" :key="sys.id" @click="detailSys = sys" class="clickable">
          <td>{{ sys.systemName }}</td>
          <td><span :class="'badge tier-' + sys.tier">{{ sys.tier.toUpperCase() }}</span></td>
          <td><span :class="'badge status-' + sys.status">{{ statusLabel(sys.status) }}</span></td>
          <td>{{ sys.rtoMinutes }}</td>
          <td>{{ sys.rpoMinutes }}</td>
          <td>{{ sys.recoveryPriority }}</td>
          <td>{{ sys.owner }}</td>
        </tr>
        <tr v-if="store.systems.length === 0">
          <td colspan="7" class="empty">システムなし</td>
        </tr>
      </tbody>
    </table>

    <!-- Detail modal -->
    <div v-if="detailSys" class="modal-overlay" @click.self="detailSys = null">
      <div class="modal">
        <h3>{{ detailSys.systemName }}</h3>
        <p class="desc">{{ detailSys.description }}</p>
        <table class="detail-table">
          <tr><th>Tier</th><td><span :class="'badge tier-' + detailSys.tier">{{ detailSys.tier.toUpperCase() }}</span></td></tr>
          <tr><th>ステータス</th><td><span :class="'badge status-' + detailSys.status">{{ statusLabel(detailSys.status) }}</span></td></tr>
          <tr><th>RTO（分）</th><td>{{ detailSys.rtoMinutes }}</td></tr>
          <tr><th>RPO（分）</th><td>{{ detailSys.rpoMinutes }}</td></tr>
          <tr><th>復旧優先度</th><td>{{ detailSys.recoveryPriority }}</td></tr>
          <tr><th>オーナー</th><td>{{ detailSys.owner }}</td></tr>
          <tr><th>登録日時</th><td>{{ formatDate(detailSys.createdAt) }}</td></tr>
        </table>
        <div class="modal-actions">
          <button @click="detailSys = null">閉じる</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSystemsStore } from '@/stores/systems'
import type { ItSystem } from '@/types'

const store = useSystemsStore()
const filterTier = ref('')
const filterStatus = ref('')
const detailSys = ref<ItSystem | null>(null)

function applyFilter() {
  store.fetchSystems(filterTier.value || undefined, filterStatus.value || undefined)
}

function statusLabel(s: ItSystem['status']) {
  const map: Record<string, string> = { normal: '正常', degraded: '劣化', down: '停止', maintenance: 'メンテ' }
  return map[s] ?? s
}

function formatDate(d?: string) {
  if (!d) return '—'
  return new Date(d).toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

onMounted(() => store.fetchSystems())
</script>

<style scoped>
.systems { padding: 1rem; }
h2 { margin-bottom: 1rem; }
.filters { display: flex; gap: 0.75rem; margin-bottom: 0.75rem; }
.summary-row { display: flex; gap: 0.75rem; margin-bottom: 1rem; }
.summary-chip { background: #1e1e2e; border: 1px solid #313244; border-radius: 6px; padding: 0.3rem 0.75rem; font-size: 0.85rem; color: #a6adc8; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th { background: #1e1e2e; padding: 0.6rem 0.75rem; text-align: left; color: #a6adc8; font-weight: 600; }
.data-table td { padding: 0.6rem 0.75rem; border-bottom: 1px solid #313244; }
.clickable { cursor: pointer; }
.clickable:hover td { background: #1e1e2e; }
.empty { text-align: center; color: #6c7086; padding: 2rem; }
.badge { padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.78rem; font-weight: 600; }
.tier-tier1 { background: #f38ba820; color: #f38ba8; }
.tier-tier2 { background: #fab38720; color: #fab387; }
.tier-tier3 { background: #89b4fa20; color: #89b4fa; }
.tier-tier4 { background: #a6adc820; color: #a6adc8; }
.status-normal { background: #a6e3a120; color: #a6e3a1; }
.status-degraded { background: #f9e2af20; color: #f9e2af; }
.status-down { background: #f38ba820; color: #f38ba8; }
.status-maintenance { background: #89b4fa20; color: #89b4fa; }
.modal-overlay { position: fixed; inset: 0; background: #00000088; display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #45475a; border-radius: 8px; padding: 1.5rem; min-width: 400px; max-width: 520px; }
.modal h3 { margin-bottom: 0.75rem; }
.desc { color: #a6adc8; font-size: 0.9rem; margin-bottom: 1rem; }
.detail-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-bottom: 1rem; }
.detail-table th { width: 130px; color: #a6adc8; padding: 0.4rem 0; text-align: left; }
.detail-table td { padding: 0.4rem 0; }
.modal-actions { display: flex; gap: 0.5rem; justify-content: flex-end; }
.error { color: #f38ba8; }
</style>
