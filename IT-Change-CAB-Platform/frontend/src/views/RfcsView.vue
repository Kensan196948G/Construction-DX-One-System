<template>
  <div class="rfcs-view">
    <div class="header-row">
      <h2>RFC 管理</h2>
      <button @click="showCreate = true">+ 新規 RFC 登録</button>
    </div>

    <div class="filter-bar">
      <select v-model="filterStatus" @change="applyFilter">
        <option value="">全ステータス</option>
        <option value="draft">下書き</option>
        <option value="pending_approval">承認待ち</option>
        <option value="cab_review">CABレビュー</option>
        <option value="approved">承認済み</option>
        <option value="rejected">却下</option>
        <option value="in_progress">実施中</option>
        <option value="completed">完了</option>
        <option value="cancelled">キャンセル</option>
      </select>
      <select v-model="filterType" @change="applyFilter">
        <option value="">全種別</option>
        <option value="normal">通常</option>
        <option value="emergency">緊急</option>
        <option value="standard">標準</option>
      </select>
      <select v-model="filterPriority" @change="applyFilter">
        <option value="">全優先度</option>
        <option value="low">低</option>
        <option value="medium">中</option>
        <option value="high">高</option>
        <option value="critical">クリティカル</option>
      </select>
    </div>

    <p v-if="rfcStore.loading">読み込み中...</p>
    <p v-else-if="rfcStore.error" class="error">{{ rfcStore.error }}</p>
    <table v-else-if="rfcStore.rfcs.length" class="data-table">
      <thead>
        <tr>
          <th>RFC番号</th>
          <th>タイトル</th>
          <th>種別</th>
          <th>優先度</th>
          <th>ステータス</th>
          <th>リスクスコア</th>
          <th>計画開始</th>
          <th>申請者</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rfc in rfcStore.rfcs" :key="rfc.id">
          <td><code>{{ rfc.rfcNumber }}</code></td>
          <td>{{ rfc.title }}</td>
          <td><span :class="['badge', 'type-' + rfc.changeType]">{{ changeTypeLabel(rfc.changeType) }}</span></td>
          <td><span :class="['badge', 'priority-' + rfc.priority]">{{ priorityLabel(rfc.priority) }}</span></td>
          <td>
            <select
              :value="rfc.status"
              @change="onStatusChange(rfc.id, ($event.target as HTMLSelectElement).value as RfcStatus)"
              class="status-select"
            >
              <option value="draft">下書き</option>
              <option value="pending_approval">承認待ち</option>
              <option value="cab_review">CABレビュー</option>
              <option value="approved">承認済み</option>
              <option value="rejected">却下</option>
              <option value="in_progress">実施中</option>
              <option value="completed">完了</option>
              <option value="cancelled">キャンセル</option>
            </select>
          </td>
          <td :class="rfc.riskScore >= 15 ? 'high-score' : ''">{{ rfc.riskScore }}</td>
          <td>{{ formatDate(rfc.plannedStart) }}</td>
          <td>{{ rfc.requester.displayName }}</td>
          <td>
            <button class="btn-sm" @click="openDetail(rfc)">詳細</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>RFC はありません。</p>

    <!-- 詳細モーダル -->
    <div v-if="detailRfc" class="modal-overlay" @click.self="detailRfc = null">
      <div class="modal">
        <h3>{{ detailRfc.rfcNumber }} — {{ detailRfc.title }}</h3>
        <dl class="detail-list">
          <dt>説明</dt><dd>{{ detailRfc.description ?? '—' }}</dd>
          <dt>対象システム</dt><dd>{{ detailRfc.targetSystems.join(', ') }}</dd>
          <dt>影響ユーザー数</dt><dd>{{ detailRfc.affectedUsers.toLocaleString() }} 名</dd>
          <dt>計画開始</dt><dd>{{ formatDate(detailRfc.plannedStart) }}</dd>
          <dt>計画終了</dt><dd>{{ formatDate(detailRfc.plannedEnd) }}</dd>
          <dt>技術リスク</dt><dd>{{ detailRfc.technicalRisk }}</dd>
          <dt>リスクスコア</dt><dd :class="detailRfc.riskScore >= 15 ? 'high-score' : ''">{{ detailRfc.riskScore }}</dd>
          <dt>ロールバック計画</dt><dd>{{ detailRfc.rollbackPlan ?? '—' }}</dd>
          <dt>申請者</dt><dd>{{ detailRfc.requester.displayName }}</dd>
        </dl>
        <button @click="detailRfc = null">閉じる</button>
      </div>
    </div>

    <!-- 新規登録モーダル -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal">
        <h3>新規 RFC 登録</h3>
        <form @submit.prevent="submitCreate">
          <div class="form-row">
            <label>タイトル *</label>
            <input v-model="form.title" required />
          </div>
          <div class="form-row">
            <label>説明</label>
            <textarea v-model="form.description" rows="3" />
          </div>
          <div class="form-row">
            <label>種別 *</label>
            <select v-model="form.changeType" required>
              <option value="normal">通常</option>
              <option value="emergency">緊急</option>
              <option value="standard">標準</option>
            </select>
          </div>
          <div class="form-row">
            <label>優先度 *</label>
            <select v-model="form.priority" required>
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
              <option value="critical">クリティカル</option>
            </select>
          </div>
          <div class="form-row">
            <label>対象システム * (カンマ区切り)</label>
            <input v-model="form.targetSystemsRaw" required placeholder="例: WebServer, DB" />
          </div>
          <div class="form-row">
            <label>計画開始 *</label>
            <input type="datetime-local" v-model="form.plannedStart" required />
          </div>
          <div class="form-row">
            <label>計画終了 *</label>
            <input type="datetime-local" v-model="form.plannedEnd" required />
          </div>
          <div class="form-row">
            <label>技術リスク *</label>
            <select v-model="form.technicalRisk" required>
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
            </select>
          </div>
          <div class="form-row">
            <label>ロールバック計画</label>
            <textarea v-model="form.rollbackPlan" rows="2" />
          </div>
          <p v-if="createError" class="error">{{ createError }}</p>
          <div class="form-actions">
            <button type="button" @click="showCreate = false">キャンセル</button>
            <button type="submit" :disabled="submitting">{{ submitting ? '送信中...' : '登録' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRfcsStore } from '@/stores/rfcs'
import type { Rfc, RfcStatus, ChangeType, ChangePriority, TechnicalRisk } from '@/types'

const rfcStore = useRfcsStore()

const filterStatus = ref<RfcStatus | ''>('')
const filterType = ref<ChangeType | ''>('')
const filterPriority = ref<ChangePriority | ''>('')
const detailRfc = ref<Rfc | null>(null)
const showCreate = ref(false)
const submitting = ref(false)
const createError = ref<string | null>(null)

const form = ref({
  title: '',
  description: '',
  changeType: 'normal' as ChangeType,
  priority: 'medium' as ChangePriority,
  targetSystemsRaw: '',
  plannedStart: '',
  plannedEnd: '',
  technicalRisk: 'low' as TechnicalRisk,
  rollbackPlan: '',
})

onMounted(() => rfcStore.fetchRfcs())

function applyFilter() {
  rfcStore.fetchRfcs(
    filterStatus.value || undefined,
    filterType.value || undefined,
    filterPriority.value || undefined,
  )
}

async function onStatusChange(id: string, status: RfcStatus) {
  await rfcStore.updateRfcStatus(id, { status })
}

function openDetail(rfc: Rfc) {
  detailRfc.value = rfc
}

async function submitCreate() {
  submitting.value = true
  createError.value = null
  const result = await rfcStore.createRfc({
    title: form.value.title,
    description: form.value.description || null,
    changeType: form.value.changeType,
    priority: form.value.priority,
    targetSystems: form.value.targetSystemsRaw.split(',').map((s) => s.trim()).filter(Boolean),
    plannedStart: new Date(form.value.plannedStart).toISOString(),
    plannedEnd: new Date(form.value.plannedEnd).toISOString(),
    technicalRisk: form.value.technicalRisk,
    rollbackPlan: form.value.rollbackPlan || null,
  })
  submitting.value = false
  if (result) {
    showCreate.value = false
    resetForm()
  } else {
    createError.value = rfcStore.error ?? '登録に失敗しました'
  }
}

function resetForm() {
  form.value = {
    title: '', description: '', changeType: 'normal', priority: 'medium',
    targetSystemsRaw: '', plannedStart: '', plannedEnd: '', technicalRisk: 'low', rollbackPlan: '',
  }
}

function changeTypeLabel(v: ChangeType): string {
  return { normal: '通常', emergency: '緊急', standard: '標準' }[v] ?? v
}
function priorityLabel(v: ChangePriority): string {
  return { low: '低', medium: '中', high: '高', critical: 'クリティカル' }[v] ?? v
}
function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}
</script>

<style scoped>
.rfcs-view { padding: 1rem; }
.header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.filter-bar { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.type-normal { background: #89b4fa; color: #1e1e2e; }
.type-emergency { background: #f38ba8; color: #1e1e2e; }
.type-standard { background: #a6e3a1; color: #1e1e2e; }
.priority-low { background: #6c7086; color: #cdd6f4; }
.priority-medium { background: #f9e2af; color: #1e1e2e; }
.priority-high { background: #fab387; color: #1e1e2e; }
.priority-critical { background: #f38ba8; color: #1e1e2e; }
.status-select { background: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 0.2rem 0.4rem; font-size: 0.8rem; }
.high-score { color: #f38ba8; font-weight: bold; }
.btn-sm { padding: 0.2rem 0.6rem; font-size: 0.8rem; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #45475a; border-radius: 8px; padding: 1.5rem; min-width: 420px; max-width: 600px; max-height: 80vh; overflow-y: auto; }
.modal h3 { margin-bottom: 1rem; color: #cdd6f4; }
.detail-list { display: grid; grid-template-columns: 140px 1fr; gap: 0.4rem 0.75rem; font-size: 0.9rem; margin-bottom: 1rem; }
.detail-list dt { color: #a6adc8; }
.detail-list dd { color: #cdd6f4; }
.form-row { display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem; }
.form-row label { font-size: 0.85rem; color: #a6adc8; }
.form-row input, .form-row select, .form-row textarea { width: 100%; }
.form-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }
.error { color: #f38ba8; font-size: 0.9rem; }
</style>
