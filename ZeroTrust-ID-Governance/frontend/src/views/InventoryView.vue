<template>
  <div class="inventory-view">
    <h2>アカウント棚卸管理</h2>

    <div class="filters">
      <select v-model="filterStatus" @change="applyFilter">
        <option value="">ステータス: すべて</option>
        <option value="draft">draft</option>
        <option value="active">active</option>
        <option value="completed">completed</option>
        <option value="cancelled">cancelled</option>
      </select>
      <button @click="showModal = true">+ 新規キャンペーン</button>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>
    <table v-else-if="store.campaigns.length" class="data-table">
      <thead>
        <tr>
          <th>キャンペーン名</th>
          <th>ステータス</th>
          <th>対象期間</th>
          <th>アカウント数</th>
          <th>レビュー済み</th>
          <th>フラグ数</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="campaign in store.campaigns" :key="campaign.id">
          <td>{{ campaign.name }}</td>
          <td><span :class="['badge', 'status-' + campaign.status]">{{ campaign.status }}</span></td>
          <td>{{ campaign.review_period_start }} 〜 {{ campaign.review_period_end }}</td>
          <td>{{ campaign.total_accounts }}</td>
          <td>{{ campaign.reviewed_count }}</td>
          <td>{{ campaign.flagged_count }}</td>
          <td class="actions">
            <button
              v-if="campaign.status === 'draft'"
              class="btn-sm btn-start"
              @click="handleStart(campaign.id)"
            >開始</button>
            <button
              v-if="campaign.status === 'active'"
              class="btn-sm btn-ok"
              @click="handleComplete(campaign.id)"
            >完了</button>
            <button
              v-if="campaign.status === 'draft' || campaign.status === 'active'"
              class="btn-sm btn-cancel"
              @click="handleCancel(campaign.id)"
            >キャンセル</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>キャンペーンはありません。</p>

    <!-- 新規キャンペーン作成モーダル -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>新規棚卸キャンペーン</h3>
        <div class="form-group">
          <label>キャンペーン名 <span class="required">*</span></label>
          <input
            v-model="form.name"
            placeholder="2026年Q1 アカウント棚卸"
            required
          />
          <span v-if="formErrors.name" class="field-error">{{ formErrors.name }}</span>
        </div>
        <div class="form-group">
          <label>説明</label>
          <textarea v-model="form.description" placeholder="（任意）棚卸の概要を入力" rows="3" />
        </div>
        <div class="form-group">
          <label>対象期間 開始 <span class="required">*</span></label>
          <input v-model="form.review_period_start" type="date" required />
          <span v-if="formErrors.review_period_start" class="field-error">{{ formErrors.review_period_start }}</span>
        </div>
        <div class="form-group">
          <label>対象期間 終了 <span class="required">*</span></label>
          <input v-model="form.review_period_end" type="date" required />
          <span v-if="formErrors.review_period_end" class="field-error">{{ formErrors.review_period_end }}</span>
        </div>
        <div class="modal-actions">
          <button @click="submitCampaign">登録</button>
          <button @click="closeModal">キャンセル</button>
        </div>
        <p v-if="store.error" class="error">{{ store.error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useInventoryStore } from '@/stores/inventory'
import type { CampaignStatus } from '@/api/inventory'

const store = useInventoryStore()
const filterStatus = ref('')
const showModal = ref(false)

const form = ref({
  name: '',
  description: '',
  review_period_start: '',
  review_period_end: '',
})

const formErrors = reactive({
  name: '',
  review_period_start: '',
  review_period_end: '',
})

onMounted(() => store.fetchCampaigns())

function applyFilter() {
  store.fetchCampaigns(filterStatus.value as CampaignStatus || undefined)
}

function validateForm(): boolean {
  formErrors.name = ''
  formErrors.review_period_start = ''
  formErrors.review_period_end = ''

  let valid = true
  if (!form.value.name.trim()) {
    formErrors.name = 'キャンペーン名は必須です'
    valid = false
  }
  if (!form.value.review_period_start) {
    formErrors.review_period_start = '開始日は必須です'
    valid = false
  }
  if (!form.value.review_period_end) {
    formErrors.review_period_end = '終了日は必須です'
    valid = false
  }
  return valid
}

async function submitCampaign() {
  if (!validateForm()) return
  const result = await store.createCampaign({
    name: form.value.name,
    description: form.value.description || null,
    review_period_start: form.value.review_period_start,
    review_period_end: form.value.review_period_end,
  })
  if (result) closeModal()
}

function closeModal() {
  showModal.value = false
  form.value = { name: '', description: '', review_period_start: '', review_period_end: '' }
  formErrors.name = ''
  formErrors.review_period_start = ''
  formErrors.review_period_end = ''
}

async function handleStart(id: string) {
  await store.startCampaign(id)
}

async function handleComplete(id: string) {
  await store.completeCampaign(id)
}

async function handleCancel(id: string) {
  await store.cancelCampaign(id)
}
</script>

<style scoped>
.inventory-view { padding: 1rem; }
.filters { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.actions { display: flex; gap: 0.35rem; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.status-draft { background: #6c7086; color: #cdd6f4; }
.status-active { background: #89b4fa; color: #1e1e2e; }
.status-completed { background: #a6e3a1; color: #1e1e2e; }
.status-cancelled { background: #f38ba8; color: #1e1e2e; }
.btn-sm { font-size: 0.75rem; padding: 0.2rem 0.5rem; }
.btn-start { background: #89b4fa; color: #1e1e2e; }
.btn-ok { background: #40a02b; }
.btn-cancel { background: #f38ba8; color: #1e1e2e; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #333; border-radius: 8px; padding: 1.5rem; min-width: 380px; }
.modal h3 { margin-bottom: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem; }
.form-group label { font-size: 0.85rem; color: #a6adc8; }
.required { color: #f38ba8; }
.field-error { color: #f38ba8; font-size: 0.78rem; }
.modal-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.error { color: #f38ba8; margin-top: 0.5rem; }
textarea { resize: vertical; }
</style>
