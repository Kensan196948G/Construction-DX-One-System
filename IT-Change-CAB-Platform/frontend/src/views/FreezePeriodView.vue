<template>
  <div class="freeze-period-view">
    <div class="header-row">
      <h2>変更凍結期間管理</h2>
      <button @click="showCreate = true">+ 新規登録</button>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>
    <table v-else-if="store.freezePeriods.length" class="data-table">
      <thead>
        <tr>
          <th>期間名</th>
          <th>開始日</th>
          <th>終了日</th>
          <th>理由</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="fp in store.freezePeriods" :key="fp.id" :class="isActive(fp) ? 'row-active' : ''">
          <td>{{ fp.title }}</td>
          <td>{{ formatDate(fp.start_date) }}</td>
          <td>{{ formatDate(fp.end_date) }}</td>
          <td>{{ fp.reason ?? '—' }}</td>
          <td>
            <button class="btn-sm btn-danger" @click="handleDelete(fp.id)">削除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>凍結期間はありません。</p>

    <!-- 新規登録モーダル -->
    <div v-if="showCreate" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h3>新規凍結期間登録</h3>
        <form @submit.prevent="submitCreate">
          <div class="form-row">
            <label>期間名 *</label>
            <input v-model="form.title" required placeholder="例: 年末年始システム凍結" />
          </div>
          <div class="form-row">
            <label>開始日 *</label>
            <input type="date" v-model="form.start_date" required />
          </div>
          <div class="form-row">
            <label>終了日 *</label>
            <input type="date" v-model="form.end_date" required />
          </div>
          <div class="form-row">
            <label>理由</label>
            <textarea v-model="form.reason" rows="3" placeholder="凍結期間の理由や背景" />
          </div>
          <p v-if="formError" class="error">{{ formError }}</p>
          <div class="form-actions">
            <button type="button" @click="closeModal">キャンセル</button>
            <button type="submit" :disabled="submitting">{{ submitting ? '登録中...' : '登録' }}</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 削除確認モーダル -->
    <div v-if="deleteTargetId" class="modal-overlay" @click.self="deleteTargetId = null">
      <div class="modal modal-confirm">
        <h3>削除確認</h3>
        <p>この凍結期間を削除してよろしいですか？</p>
        <div class="form-actions">
          <button type="button" @click="deleteTargetId = null">キャンセル</button>
          <button class="btn-danger" @click="confirmDelete" :disabled="deleting">{{ deleting ? '削除中...' : '削除' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFreezePeriodStore } from '@/stores/freezePeriods'
import type { FreezePeriod } from '@/api/freezePeriods'

const store = useFreezePeriodStore()

const showCreate = ref(false)
const submitting = ref(false)
const formError = ref<string | null>(null)
const deleteTargetId = ref<string | null>(null)
const deleting = ref(false)

const form = ref({
  title: '',
  start_date: '',
  end_date: '',
  reason: '',
})

onMounted(() => store.fetchFreezePeriods())

function closeModal() {
  showCreate.value = false
  formError.value = null
  resetForm()
}

function resetForm() {
  form.value = { title: '', start_date: '', end_date: '', reason: '' }
}

async function submitCreate() {
  formError.value = null
  submitting.value = true
  const result = await store.createFreezePeriod({
    title: form.value.title,
    start_date: form.value.start_date,
    end_date: form.value.end_date,
    reason: form.value.reason || undefined,
  })
  submitting.value = false
  if (result) {
    closeModal()
  } else {
    formError.value = store.error ?? '登録に失敗しました'
  }
}

function handleDelete(id: string) {
  deleteTargetId.value = id
}

async function confirmDelete() {
  if (!deleteTargetId.value) return
  deleting.value = true
  await store.deleteFreezePeriod(deleteTargetId.value)
  deleting.value = false
  deleteTargetId.value = null
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('ja-JP')
}

function isActive(fp: FreezePeriod): boolean {
  const now = new Date()
  const start = new Date(fp.start_date)
  const end = new Date(fp.end_date)
  return now >= start && now <= end
}
</script>

<style scoped>
.freeze-period-view { padding: 1rem; }
.header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.row-active { background: rgba(166, 227, 161, 0.08); }
.btn-sm { padding: 0.2rem 0.6rem; font-size: 0.8rem; }
.btn-danger { background: #45213a; color: #f38ba8; border-color: #6e3050; }
.btn-danger:hover { background: #6e3050; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #45475a; border-radius: 8px; padding: 1.5rem; min-width: 400px; max-width: 540px; max-height: 80vh; overflow-y: auto; }
.modal-confirm { min-width: 300px; max-width: 400px; }
.modal h3 { margin-bottom: 1rem; color: #cdd6f4; }
.modal p { color: #cdd6f4; margin-bottom: 1rem; }
.form-row { display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem; }
.form-row label { font-size: 0.85rem; color: #a6adc8; }
.form-row input, .form-row select, .form-row textarea { width: 100%; }
.form-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }
.error { color: #f38ba8; font-size: 0.9rem; }
</style>
