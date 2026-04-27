<template>
  <div class="risks-view">
    <div class="header">
      <h1>リスク管理</h1>
      <button @click="showForm = true">+ リスク登録</button>
    </div>

    <div class="filters">
      <select v-model="statusFilter" @change="() => store.fetchRisks(statusFilter || undefined)">
        <option value="">すべてのステータス</option>
        <option value="open">Open</option>
        <option value="mitigated">Mitigated</option>
        <option value="accepted">Accepted</option>
        <option value="closed">Closed</option>
      </select>
    </div>

    <div v-if="store.loading" class="loading">読み込み中...</div>
    <div v-else-if="store.error" class="error">{{ store.error }}</div>

    <table v-else class="risks-table">
      <thead>
        <tr>
          <th>タイトル</th>
          <th>カテゴリ</th>
          <th>スコア</th>
          <th>ステータス</th>
          <th>担当者</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="risk in store.risks" :key="risk.id" :class="riskClass(risk.risk_score)">
          <td>{{ risk.title }}</td>
          <td>{{ risk.category || '-' }}</td>
          <td><span class="score-badge">{{ risk.risk_score }}</span></td>
          <td><span :class="['status-badge', risk.status]">{{ risk.status }}</span></td>
          <td>{{ risk.owner || '-' }}</td>
        </tr>
        <tr v-if="store.risks.length === 0">
          <td colspan="5" class="empty">リスクが登録されていません</td>
        </tr>
      </tbody>
    </table>

    <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false">
      <div class="modal">
        <h2>リスク登録</h2>
        <form @submit.prevent="submitRisk">
          <label>タイトル * <input v-model="form.title" required /></label>
          <label>説明 <textarea v-model="form.description" /></label>
          <label>カテゴリ <input v-model="form.category" /></label>
          <label>可能性 (1-5)
            <input v-model.number="form.likelihood" type="number" min="1" max="5" required />
          </label>
          <label>影響度 (1-5)
            <input v-model.number="form.impact" type="number" min="1" max="5" required />
          </label>
          <label>担当者 <input v-model="form.owner" /></label>
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
import { ref, onMounted, reactive } from 'vue'
import { useRisksStore } from '@/stores/risks'
import type { Risk } from '@/types'

const store = useRisksStore()
const statusFilter = ref('')
const showForm = ref(false)
const form = reactive({ title: '', description: '', category: '', likelihood: 3, impact: 3, owner: '' })

const riskClass = (score: number) => score >= 20 ? 'row-critical' : score >= 15 ? 'row-high' : ''

async function submitRisk() {
  const result = await store.createRisk({ ...form })
  if (result) {
    showForm.value = false
    Object.assign(form, { title: '', description: '', category: '', likelihood: 3, impact: 3, owner: '' })
  }
}

onMounted(() => store.fetchRisks())
</script>

<style scoped>
.risks-view { padding: 1.5rem; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.filters { margin-bottom: 1rem; }
.risks-table { width: 100%; border-collapse: collapse; }
.risks-table th, .risks-table td { padding: 0.75rem; border-bottom: 1px solid #eee; text-align: left; }
.risks-table th { background: #f5f5f5; font-weight: 600; }
.row-critical td:first-child { border-left: 4px solid #e53935; }
.row-high td:first-child { border-left: 4px solid #fb8c00; }
.score-badge { background: #e53935; color: #fff; padding: 2px 8px; border-radius: 12px; font-size: 0.85rem; }
.status-badge { padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; }
.status-badge.open { background: #ffebee; color: #c62828; }
.status-badge.mitigated { background: #e8f5e9; color: #2e7d32; }
.status-badge.accepted { background: #fff8e1; color: #f57f17; }
.status-badge.closed { background: #f5f5f5; color: #616161; }
.empty { text-align: center; color: #999; padding: 2rem; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; padding: 2rem; border-radius: 8px; min-width: 360px; }
.modal form { display: flex; flex-direction: column; gap: 0.75rem; }
.modal label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.9rem; }
.modal input, .modal textarea { padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.5rem; }
.loading, .error { padding: 1rem; }
.error { color: #e53935; }
</style>
