<template>
  <div class="incidents">
    <div class="page-header">
      <h2>インシデント管理</h2>
      <button @click="showCreate = true">+ 新規インシデント</button>
    </div>

    <div class="filters">
      <select v-model="filterSeverity" @change="applyFilter">
        <option value="">深刻度: すべて</option>
        <option value="critical">クリティカル</option>
        <option value="high">高</option>
        <option value="medium">中</option>
        <option value="low">低</option>
      </select>
      <select v-model="filterStatus" @change="applyFilter">
        <option value="">ステータス: すべて</option>
        <option value="open">オープン</option>
        <option value="investigating">調査中</option>
        <option value="bcp_activated">BCP発動中</option>
        <option value="recovering">復旧中</option>
        <option value="resolved">解決済み</option>
        <option value="closed">クローズ</option>
      </select>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>

    <table v-else class="data-table">
      <thead>
        <tr>
          <th>番号</th>
          <th>タイトル</th>
          <th>深刻度</th>
          <th>ステータス</th>
          <th>影響システム数</th>
          <th>BCP</th>
          <th>発生日時</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="inc in store.incidents" :key="inc.id" @click="detailInc = inc" class="clickable">
          <td>{{ inc.incidentNumber }}</td>
          <td>{{ inc.title }}</td>
          <td><span :class="'badge sev-' + inc.severity">{{ inc.severity }}</span></td>
          <td>
            <select
              :value="inc.status"
              @change="onStatusChange(inc.id, ($event.target as HTMLSelectElement).value)"
              @click.stop
            >
              <option value="open">オープン</option>
              <option value="investigating">調査中</option>
              <option value="bcp_activated">BCP発動</option>
              <option value="recovering">復旧中</option>
              <option value="resolved">解決済み</option>
              <option value="closed">クローズ</option>
            </select>
          </td>
          <td>{{ inc.affectedSystemsCount }}</td>
          <td><span :class="inc.bcpActivated ? 'badge bcp-on' : 'badge bcp-off'">{{ inc.bcpActivated ? '発動中' : '—' }}</span></td>
          <td>{{ formatDate(inc.declaredAt) }}</td>
        </tr>
        <tr v-if="store.incidents.length === 0">
          <td colspan="7" class="empty">インシデントなし</td>
        </tr>
      </tbody>
    </table>

    <!-- Detail modal -->
    <div v-if="detailInc" class="modal-overlay" @click.self="detailInc = null">
      <div class="modal">
        <h3>{{ detailInc.incidentNumber }} — {{ detailInc.title }}</h3>
        <p class="desc">{{ detailInc.description }}</p>
        <table class="detail-table">
          <tr><th>深刻度</th><td><span :class="'badge sev-' + detailInc.severity">{{ detailInc.severity }}</span></td></tr>
          <tr><th>ステータス</th><td>{{ detailInc.status }}</td></tr>
          <tr><th>BCP発動</th><td>{{ detailInc.bcpActivated ? 'はい' : 'いいえ' }}</td></tr>
          <tr><th>影響システム数</th><td>{{ detailInc.affectedSystemsCount }}</td></tr>
          <tr><th>発生日時</th><td>{{ formatDate(detailInc.declaredAt) }}</td></tr>
          <tr v-if="detailInc.resolvedAt"><th>解決日時</th><td>{{ formatDate(detailInc.resolvedAt) }}</td></tr>
        </table>
        <div class="modal-actions">
          <button
            v-if="!detailInc.bcpActivated && detailInc.status !== 'resolved' && detailInc.status !== 'closed'"
            class="btn-danger"
            @click="activateBcp(detailInc.id)"
          >BCP 発動</button>
          <button @click="detailInc = null">閉じる</button>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal">
        <h3>新規インシデント登録</h3>
        <div class="form-grid">
          <label>タイトル<input v-model="form.title" /></label>
          <label>深刻度
            <select v-model="form.severity">
              <option value="critical">クリティカル</option>
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </label>
          <label class="span2">説明<textarea v-model="form.description" rows="3"></textarea></label>
        </div>
        <p v-if="createError" class="error">{{ createError }}</p>
        <div class="modal-actions">
          <button @click="submitCreate" :disabled="creating">{{ creating ? '登録中...' : '登録' }}</button>
          <button @click="showCreate = false">キャンセル</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useIncidentsStore } from '@/stores/incidents'
import type { Incident } from '@/types'

const store = useIncidentsStore()
const filterSeverity = ref('')
const filterStatus = ref('')
const detailInc = ref<Incident | null>(null)
const showCreate = ref(false)
const creating = ref(false)
const createError = ref<string | null>(null)

const form = ref({ title: '', description: '', severity: 'high' as Incident['severity'] })

function applyFilter() {
  store.fetchIncidents(
    (filterStatus.value || undefined) as Incident['status'] | undefined,
    (filterSeverity.value || undefined) as Incident['severity'] | undefined,
  )
}

async function onStatusChange(id: string, newStatus: string) {
  await store.updateIncidentStatus(id, { status: newStatus as Incident['status'] })
}

async function activateBcp(id: string) {
  await store.updateIncidentStatus(id, { status: 'bcp_activated' })
  if (detailInc.value?.id === id) {
    detailInc.value = store.incidents.find((i) => i.id === id) ?? null
  }
}

async function submitCreate() {
  if (!form.value.title.trim()) { createError.value = 'タイトルを入力してください'; return }
  creating.value = true
  createError.value = null
  const ok = await store.createIncident(form.value)
  creating.value = false
  if (ok) {
    showCreate.value = false
    form.value = { title: '', description: '', severity: 'high' }
  } else {
    createError.value = store.error ?? '登録に失敗しました'
  }
}

function formatDate(d?: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => store.fetchIncidents())
</script>

<style scoped>
.incidents { padding: 1rem; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.filters { display: flex; gap: 0.75rem; margin-bottom: 1rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th { background: #1e1e2e; padding: 0.6rem 0.75rem; text-align: left; color: #a6adc8; font-weight: 600; }
.data-table td { padding: 0.6rem 0.75rem; border-bottom: 1px solid #313244; }
.clickable { cursor: pointer; }
.clickable:hover td { background: #1e1e2e; }
.empty { text-align: center; color: #6c7086; padding: 2rem; }
.badge { padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.78rem; font-weight: 600; }
.sev-critical { background: #f38ba820; color: #f38ba8; }
.sev-high { background: #fab38720; color: #fab387; }
.sev-medium { background: #f9e2af20; color: #f9e2af; }
.sev-low { background: #a6e3a120; color: #a6e3a1; }
.bcp-on { background: #cba6f720; color: #cba6f7; }
.bcp-off { color: #6c7086; }
.modal-overlay { position: fixed; inset: 0; background: #00000088; display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #45475a; border-radius: 8px; padding: 1.5rem; min-width: 400px; max-width: 560px; }
.modal h3 { margin-bottom: 0.75rem; }
.desc { color: #a6adc8; font-size: 0.9rem; margin-bottom: 1rem; }
.detail-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-bottom: 1rem; }
.detail-table th { width: 130px; color: #a6adc8; padding: 0.4rem 0; text-align: left; }
.detail-table td { padding: 0.4rem 0; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1rem; }
.form-grid label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.85rem; color: #a6adc8; }
.span2 { grid-column: span 2; }
.modal-actions { display: flex; gap: 0.5rem; justify-content: flex-end; }
.btn-danger { background: #f38ba820; color: #f38ba8; border-color: #f38ba860; }
.btn-danger:hover { background: #f38ba840; }
.error { color: #f38ba8; font-size: 0.85rem; }
</style>
