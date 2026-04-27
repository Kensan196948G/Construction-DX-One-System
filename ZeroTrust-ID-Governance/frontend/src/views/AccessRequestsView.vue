<template>
  <div class="requests-view">
    <h2>アクセス申請管理</h2>

    <div class="filters">
      <select v-model="filterStatus" @change="applyFilter">
        <option value="">ステータス: すべて</option>
        <option value="pending">pending</option>
        <option value="approved">approved</option>
        <option value="rejected">rejected</option>
        <option value="in_review">in_review</option>
        <option value="expired">expired</option>
        <option value="cancelled">cancelled</option>
      </select>
      <button @click="showModal = true">+ 新規申請</button>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>
    <table v-else-if="store.requests.length" class="data-table">
      <thead>
        <tr>
          <th>申請者</th>
          <th>ロール</th>
          <th>リソース</th>
          <th>理由</th>
          <th>ステータス</th>
          <th>申請日時</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="req in store.requests" :key="req.id">
          <td>{{ req.requester_name }}</td>
          <td>{{ req.requested_role }}</td>
          <td>{{ req.resource ?? '—' }}</td>
          <td class="reason-cell">{{ req.reason }}</td>
          <td><span :class="['badge', 'status-' + req.status]">{{ req.status }}</span></td>
          <td>{{ formatDate(req.created_at) }}</td>
          <td>
            <template v-if="req.status === 'pending' || req.status === 'in_review'">
              <button class="btn-sm btn-ok" @click="approve(req.id)">承認</button>
              <button class="btn-sm btn-ng" @click="reject(req.id)">却下</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>申請はありません。</p>

    <!-- 新規申請モーダル -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>新規アクセス申請</h3>
        <div class="form-group">
          <label>申請ロール</label>
          <input v-model="form.requested_role" placeholder="read_only / admin / etc." />
        </div>
        <div class="form-group">
          <label>リソース（任意）</label>
          <input v-model="form.resource" placeholder="例: /reports/financial" />
        </div>
        <div class="form-group">
          <label>理由</label>
          <textarea v-model="form.reason" placeholder="申請理由を入力してください" rows="3" />
        </div>
        <div class="form-group">
          <label>有効期限（任意）</label>
          <input v-model="form.expires_at" type="datetime-local" />
        </div>
        <div class="modal-actions">
          <button @click="submitRequest">申請</button>
          <button @click="showModal = false">キャンセル</button>
        </div>
        <p v-if="store.error" class="error">{{ store.error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAccessRequestsStore } from '@/stores/accessRequests'

const store = useAccessRequestsStore()
const filterStatus = ref('')
const showModal = ref(false)
const form = ref({ requested_role: '', resource: '', reason: '', expires_at: '' })

onMounted(() => store.fetchRequests())

function applyFilter() {
  store.fetchRequests(filterStatus.value || undefined)
}

async function approve(id: string) {
  await store.approveRequest(id)
}

async function reject(id: string) {
  await store.rejectRequest(id)
}

async function submitRequest() {
  const payload = {
    requested_role: form.value.requested_role,
    resource: form.value.resource || null,
    reason: form.value.reason,
    expires_at: form.value.expires_at || null,
  }
  const result = await store.createRequest(payload)
  if (result) {
    showModal.value = false
    form.value = { requested_role: '', resource: '', reason: '', expires_at: '' }
  }
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}
</script>

<style scoped>
.requests-view { padding: 1rem; }
.filters { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.reason-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.status-pending { background: #fab387; color: #1e1e2e; }
.status-approved { background: #a6e3a1; color: #1e1e2e; }
.status-rejected { background: #f38ba8; color: #1e1e2e; }
.status-in_review { background: #89b4fa; color: #1e1e2e; }
.status-expired { background: #6c7086; color: #cdd6f4; }
.status-cancelled { background: #45475a; color: #cdd6f4; }
.btn-sm { font-size: 0.75rem; padding: 0.2rem 0.5rem; margin-right: 0.25rem; }
.btn-ok { background: #40a02b; }
.btn-ng { background: #d20f39; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #333; border-radius: 8px; padding: 1.5rem; min-width: 400px; }
.modal h3 { margin-bottom: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem; }
.form-group label { font-size: 0.85rem; color: #a6adc8; }
.form-group textarea { resize: vertical; }
.modal-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.error { color: #f38ba8; margin-top: 0.5rem; }
</style>
