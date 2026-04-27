<template>
  <div class="audits-view">
    <div class="header">
      <h1>監査管理</h1>
      <button @click="showAuditForm = true">+ 監査登録</button>
    </div>

    <div class="filters">
      <select v-model="statusFilter">
        <option value="">すべてのステータス</option>
        <option value="planned">Planned</option>
        <option value="in_progress">In Progress</option>
        <option value="completed">Completed</option>
        <option value="cancelled">Cancelled</option>
      </select>
    </div>

    <div v-if="loading" class="loading">読み込み中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else class="audit-list">
      <div
        v-for="audit in filteredAudits"
        :key="audit.id"
        class="audit-card"
      >
        <div class="audit-header" @click="toggleAudit(audit.id)">
          <div class="audit-info">
            <span class="audit-title">{{ audit.title }}</span>
            <span :class="['status-badge', audit.status]">{{ audit.status }}</span>
          </div>
          <div class="audit-meta">
            <span v-if="audit.auditor">監査人: {{ audit.auditor }}</span>
            <span v-if="audit.planned_date">予定: {{ audit.planned_date }}</span>
            <span class="finding-count">指摘: {{ audit.findings.length }}件</span>
            <span class="expand-icon">{{ expandedAudits.has(audit.id) ? '▲' : '▼' }}</span>
          </div>
        </div>

        <div v-if="expandedAudits.has(audit.id)" class="findings-section">
          <div class="findings-toolbar">
            <span class="findings-label">指摘事項</span>
            <button class="small-btn" @click="openFindingForm(audit.id)">+ 指摘追加</button>
          </div>
          <table v-if="audit.findings.length > 0" class="findings-table">
            <thead>
              <tr>
                <th>タイトル</th>
                <th>重大度</th>
                <th>ステータス</th>
                <th>説明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="finding in audit.findings" :key="finding.id" :class="'sev-' + finding.severity">
                <td>{{ finding.title }}</td>
                <td><span :class="['sev-badge', finding.severity]">{{ finding.severity }}</span></td>
                <td><span :class="['finding-status', finding.status]">{{ finding.status }}</span></td>
                <td class="desc-cell">{{ finding.description || '-' }}</td>
              </tr>
            </tbody>
          </table>
          <p v-else class="empty-findings">指摘事項はありません</p>
        </div>
      </div>

      <div v-if="filteredAudits.length === 0" class="empty">監査が登録されていません</div>
    </div>

    <!-- Audit form modal -->
    <div v-if="showAuditForm" class="modal-backdrop" @click.self="showAuditForm = false">
      <div class="modal">
        <h2>監査登録</h2>
        <form @submit.prevent="submitAudit">
          <label>タイトル * <input v-model="auditForm.title" required /></label>
          <label>スコープ <textarea v-model="auditForm.scope" /></label>
          <label>監査人 <input v-model="auditForm.auditor" /></label>
          <label>予定日 <input v-model="auditForm.planned_date" type="date" /></label>
          <div class="modal-actions">
            <button type="button" @click="showAuditForm = false">キャンセル</button>
            <button type="submit">登録</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Finding form modal -->
    <div v-if="showFindingForm" class="modal-backdrop" @click.self="showFindingForm = false">
      <div class="modal">
        <h2>指摘登録</h2>
        <form @submit.prevent="submitFinding">
          <label>タイトル * <input v-model="findingForm.title" required /></label>
          <label>重大度
            <select v-model="findingForm.severity">
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>
          </label>
          <label>説明 <textarea v-model="findingForm.description" /></label>
          <div class="modal-actions">
            <button type="button" @click="showFindingForm = false">キャンセル</button>
            <button type="submit">登録</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { auditsApi } from '@/api/audits'
import type { Audit } from '@/types'

const audits = ref<Audit[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const statusFilter = ref('')
const expandedAudits = ref(new Set<string>())
const showAuditForm = ref(false)
const showFindingForm = ref(false)
const activeFindingAuditId = ref<string | null>(null)

const auditForm = reactive({ title: '', scope: '', auditor: '', planned_date: '' })
const findingForm = reactive({ title: '', severity: 'medium', description: '' })

const filteredAudits = computed(() =>
  statusFilter.value
    ? audits.value.filter((a) => a.status === statusFilter.value)
    : audits.value,
)

function toggleAudit(id: string) {
  if (expandedAudits.value.has(id)) {
    expandedAudits.value.delete(id)
  } else {
    expandedAudits.value.add(id)
  }
}

function openFindingForm(auditId: string) {
  activeFindingAuditId.value = auditId
  Object.assign(findingForm, { title: '', severity: 'medium', description: '' })
  showFindingForm.value = true
}

async function loadAudits() {
  loading.value = true
  error.value = null
  try {
    audits.value = await auditsApi.list()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '監査の取得に失敗しました'
  } finally {
    loading.value = false
  }
}

async function submitAudit() {
  try {
    const created = await auditsApi.create({ ...auditForm })
    audits.value.unshift(created)
    showAuditForm.value = false
    Object.assign(auditForm, { title: '', scope: '', auditor: '', planned_date: '' })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '監査の登録に失敗しました'
  }
}

async function submitFinding() {
  if (!activeFindingAuditId.value) return
  try {
    const finding = await auditsApi.createFinding(activeFindingAuditId.value, { ...findingForm })
    const audit = audits.value.find((a) => a.id === activeFindingAuditId.value)
    if (audit) audit.findings.push(finding)
    showFindingForm.value = false
  } catch (e) {
    error.value = e instanceof Error ? e.message : '指摘の登録に失敗しました'
  }
}

onMounted(loadAudits)
</script>

<style scoped>
.audits-view { padding: 1.5rem; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.filters { margin-bottom: 1rem; }
.audit-list { display: flex; flex-direction: column; gap: 0.75rem; }
.audit-card { border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }
.audit-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem; background: #fafafa; cursor: pointer; }
.audit-header:hover { background: #f0f0f0; }
.audit-info { display: flex; align-items: center; gap: 0.75rem; }
.audit-title { font-weight: 600; }
.audit-meta { display: flex; align-items: center; gap: 1rem; font-size: 0.85rem; color: #666; }
.expand-icon { font-size: 0.75rem; }
.status-badge { padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; }
.status-badge.planned { background: #e3f2fd; color: #1565c0; }
.status-badge.in_progress { background: #fff8e1; color: #f57f17; }
.status-badge.completed { background: #e8f5e9; color: #2e7d32; }
.status-badge.cancelled { background: #f5f5f5; color: #757575; }
.finding-count { background: #ede7f6; color: #4527a0; padding: 2px 8px; border-radius: 12px; }
.findings-section { padding: 1rem; border-top: 1px solid #eee; }
.findings-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.findings-label { font-weight: 600; font-size: 0.9rem; }
.small-btn { padding: 4px 12px; font-size: 0.85rem; cursor: pointer; border: 1px solid #1565c0; background: #fff; color: #1565c0; border-radius: 4px; }
.small-btn:hover { background: #e3f2fd; }
.findings-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.findings-table th, .findings-table td { padding: 0.5rem; border-bottom: 1px solid #eee; text-align: left; }
.findings-table th { background: #f5f5f5; font-weight: 600; }
.desc-cell { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #666; }
.sev-badge { padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
.sev-badge.critical { background: #b71c1c; color: #fff; }
.sev-badge.high { background: #e53935; color: #fff; }
.sev-badge.medium { background: #fb8c00; color: #fff; }
.sev-badge.low { background: #fdd835; color: #333; }
.sev-badge.info { background: #e3f2fd; color: #1565c0; }
.finding-status { padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; }
.finding-status.open { background: #ffebee; color: #c62828; }
.finding-status.in_remediation { background: #fff8e1; color: #f57f17; }
.finding-status.resolved { background: #e8f5e9; color: #2e7d32; }
.finding-status.accepted { background: #f5f5f5; color: #616161; }
.empty-findings { color: #999; font-size: 0.9rem; text-align: center; padding: 0.5rem; }
.empty { text-align: center; color: #999; padding: 2rem; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; padding: 2rem; border-radius: 8px; min-width: 380px; }
.modal form { display: flex; flex-direction: column; gap: 0.75rem; }
.modal label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.9rem; }
.modal input, .modal select, .modal textarea { padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.5rem; }
.loading, .error { padding: 1rem; }
.error { color: #e53935; }
</style>
