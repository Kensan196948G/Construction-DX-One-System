<template>
  <div class="alerts-view">
    <h2>アラート管理</h2>

    <div class="toolbar">
      <label>
        ステータス:
        <select v-model="statusFilter" @change="loadAlerts">
          <option value="">すべて</option>
          <option value="open">open</option>
          <option value="investigating">investigating</option>
          <option value="resolved">resolved</option>
          <option value="false_positive">false_positive</option>
        </select>
      </label>
      <label>
        重大度:
        <select v-model="severityFilter" @change="loadAlerts">
          <option value="">すべて</option>
          <option value="critical">critical</option>
          <option value="high">high</option>
          <option value="medium">medium</option>
          <option value="low">low</option>
        </select>
      </label>
      <button @click="loadAlerts">更新</button>
      <button @click="showCreateModal = true">＋ 新規アラート</button>
    </div>

    <p v-if="loading">読み込み中...</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <table v-else-if="store.alerts.length" class="data-table">
      <thead>
        <tr>
          <th>タイトル</th>
          <th>重大度</th>
          <th>ステータス</th>
          <th>リスクスコア</th>
          <th>ルール名</th>
          <th>検知時刻</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="alert in store.alerts" :key="alert.id">
          <td>{{ alert.title }}</td>
          <td><span :class="['badge', 'sev-' + alert.severity]">{{ alert.severity }}</span></td>
          <td>
            <select :value="alert.status" @change="onStatusChange(alert.id, ($event.target as HTMLSelectElement).value as AlertStatus)">
              <option value="open">open</option>
              <option value="investigating">investigating</option>
              <option value="resolved">resolved</option>
              <option value="false_positive">false_positive</option>
            </select>
          </td>
          <td>{{ alert.risk_score }}</td>
          <td>{{ alert.rule_name ?? '-' }}</td>
          <td>{{ formatDate(alert.detected_at) }}</td>
          <td>
            <span v-if="alert.mitre_technique" class="mitre-tag">{{ alert.mitre_technique }}</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>アラートはありません。</p>

    <!-- Create Alert Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <h3>新規アラート登録</h3>
        <form @submit.prevent="submitCreate">
          <label>タイトル: <input v-model="form.title" required /></label>
          <label>
            重大度:
            <select v-model="form.severity">
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
              <option value="critical">critical</option>
            </select>
          </label>
          <label>ルール名: <input v-model="form.rule_name" /></label>
          <label>説明: <textarea v-model="form.description" rows="3"></textarea></label>
          <div class="modal-actions">
            <button type="submit">登録</button>
            <button type="button" @click="showCreateModal = false">キャンセル</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAlertsStore } from '@/stores/alerts'
import type { AlertStatus, AlertSeverity } from '@/types'

const store = useAlertsStore()
const loading = ref(false)
const error = ref<string | null>(null)
const statusFilter = ref<AlertStatus | ''>('')
const severityFilter = ref<AlertSeverity | ''>('')
const showCreateModal = ref(false)

const form = ref({
  title: '',
  severity: 'medium' as AlertSeverity,
  rule_name: '',
  description: '',
})

async function loadAlerts() {
  loading.value = true
  error.value = null
  try {
    await store.fetchAlerts(statusFilter.value || undefined, severityFilter.value || undefined)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load alerts'
  } finally {
    loading.value = false
  }
}

async function onStatusChange(id: string, status: AlertStatus) {
  await store.updateAlertStatus(id, status)
}

async function submitCreate() {
  const result = await store.createAlert({
    title: form.value.title,
    severity: form.value.severity,
    rule_name: form.value.rule_name || null,
    description: form.value.description || null,
  })
  if (result) {
    showCreateModal.value = false
    form.value = { title: '', severity: 'medium', rule_name: '', description: '' }
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}

onMounted(loadAlerts)
</script>

<style scoped>
.alerts-view { padding: 1rem; }
.toolbar { display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.4rem 0.6rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.sev-critical { background: #f38ba8; color: #1e1e2e; }
.sev-high { background: #fab387; color: #1e1e2e; }
.sev-medium { background: #f9e2af; color: #1e1e2e; }
.sev-low { background: #a6e3a1; color: #1e1e2e; }
.mitre-tag { font-size: 0.7rem; background: #313244; padding: 0.15rem 0.4rem; border-radius: 3px; }
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: #1e1e2e; border: 1px solid #45475a; border-radius: 8px;
  padding: 1.5rem; min-width: 400px;
}
.modal h3 { margin-top: 0; }
.modal label { display: block; margin-bottom: 0.75rem; }
.modal input, .modal select, .modal textarea {
  display: block; width: 100%; margin-top: 0.25rem;
  background: #313244; border: 1px solid #45475a; color: #cdd6f4;
  padding: 0.4rem; border-radius: 4px;
}
.modal-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }
.error { color: #f38ba8; }
</style>
