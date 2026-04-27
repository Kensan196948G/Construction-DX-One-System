<template>
  <div class="compliance-view">
    <div class="header">
      <h1>コンプライアンス管理</h1>
      <button @click="showForm = true">+ 管理策登録</button>
    </div>

    <div class="filters">
      <select v-model="statusFilter" @change="applyFilter">
        <option value="">すべてのステータス</option>
        <option value="not_started">Not Started</option>
        <option value="in_progress">In Progress</option>
        <option value="implemented">Implemented</option>
        <option value="verified">Verified</option>
      </select>
    </div>

    <div v-if="loading" class="loading">読み込み中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <table v-else class="controls-table">
      <thead>
        <tr>
          <th>管理策番号</th>
          <th>タイトル</th>
          <th>ドメイン</th>
          <th>適用可否</th>
          <th>実装ステータス</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="control in filteredControls" :key="control.id">
          <td><code>{{ control.control_number }}</code></td>
          <td>{{ control.title }}</td>
          <td>{{ control.domain }}</td>
          <td>
            <span :class="['applicability-badge', control.applicability]">
              {{ control.applicability === 'applicable' ? '適用' : '適用外' }}
            </span>
          </td>
          <td>
            <select
              :value="control.implementation_status"
              class="status-select"
              :class="control.implementation_status"
              @change="(e) => updateStatus(control.id, (e.target as HTMLSelectElement).value as Control['implementation_status'])"
            >
              <option value="not_started">Not Started</option>
              <option value="in_progress">In Progress</option>
              <option value="implemented">Implemented</option>
              <option value="verified">Verified</option>
            </select>
          </td>
        </tr>
        <tr v-if="filteredControls.length === 0">
          <td colspan="5" class="empty">管理策が登録されていません</td>
        </tr>
      </tbody>
    </table>

    <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false">
      <div class="modal">
        <h2>管理策登録</h2>
        <form @submit.prevent="submitControl">
          <label>管理策番号 * <input v-model="form.control_number" required placeholder="例: A.5.1" /></label>
          <label>タイトル * <input v-model="form.title" required /></label>
          <label>ドメイン * <input v-model="form.domain" required /></label>
          <label>適用可否
            <select v-model="form.applicability">
              <option value="applicable">適用</option>
              <option value="not_applicable">適用外</option>
            </select>
          </label>
          <label>説明 <textarea v-model="form.description" /></label>
          <div class="modal-actions">
            <button type="button" @click="showForm = false">キャンセル</button>
            <button type="submit">登録</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { complianceApi } from '@/api/compliance'
import type { Control, ControlCreate } from '@/types'

const controls = ref<Control[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const statusFilter = ref('')
const showForm = ref(false)
const form: ControlCreate = reactive({ control_number: '', title: '', domain: '', applicability: 'applicable', description: '' })

const filteredControls = computed(() =>
  statusFilter.value
    ? controls.value.filter((c) => c.implementation_status === statusFilter.value)
    : controls.value,
)

async function loadControls() {
  loading.value = true
  error.value = null
  try {
    controls.value = await complianceApi.list()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '管理策の取得に失敗しました'
  } finally {
    loading.value = false
  }
}

function applyFilter() {
  // filtered via computed
}

async function updateStatus(id: string, status: Control['implementation_status']) {
  const control = controls.value.find((c) => c.id === id)
  if (!control) return
  try {
    const updated = await complianceApi.update(id, { ...control, implementation_status: status })
    const idx = controls.value.findIndex((c) => c.id === id)
    if (idx !== -1) controls.value[idx] = updated
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'ステータスの更新に失敗しました'
  }
}

async function submitControl() {
  try {
    const created = await complianceApi.create(form as ControlCreate)
    controls.value.unshift(created)
    showForm.value = false
    Object.assign(form, { control_number: '', title: '', domain: '', applicability: 'applicable', description: '' })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '管理策の登録に失敗しました'
  }
}

onMounted(loadControls)
</script>

<style scoped>
.compliance-view { padding: 1.5rem; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.filters { margin-bottom: 1rem; }
.controls-table { width: 100%; border-collapse: collapse; }
.controls-table th, .controls-table td { padding: 0.75rem; border-bottom: 1px solid #eee; text-align: left; }
.controls-table th { background: #f5f5f5; font-weight: 600; }
code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; }
.applicability-badge { padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; }
.applicability-badge.applicable { background: #e8f5e9; color: #2e7d32; }
.applicability-badge.not_applicable { background: #f5f5f5; color: #757575; }
.status-select { border: 1px solid #ccc; border-radius: 4px; padding: 4px 8px; font-size: 0.85rem; cursor: pointer; }
.status-select.not_started { background: #ffebee; color: #c62828; border-color: #ef9a9a; }
.status-select.in_progress { background: #fff8e1; color: #f57f17; border-color: #ffe082; }
.status-select.implemented { background: #e3f2fd; color: #1565c0; border-color: #90caf9; }
.status-select.verified { background: #e8f5e9; color: #2e7d32; border-color: #a5d6a7; }
.empty { text-align: center; color: #999; padding: 2rem; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; padding: 2rem; border-radius: 8px; min-width: 400px; }
.modal form { display: flex; flex-direction: column; gap: 0.75rem; }
.modal label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.9rem; }
.modal input, .modal select, .modal textarea { padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.5rem; }
.loading, .error { padding: 1rem; }
.error { color: #e53935; }
</style>
