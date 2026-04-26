<template>
  <div class="exercises">
    <h2>BCP 演習管理</h2>

    <div class="filters">
      <select v-model="filterStatus" @change="applyFilter">
        <option value="">ステータス: すべて</option>
        <option value="planned">計画済み</option>
        <option value="in_progress">実施中</option>
        <option value="completed">完了</option>
        <option value="cancelled">キャンセル</option>
      </select>
      <select v-model="filterType" @change="applyFilter">
        <option value="">種別: すべて</option>
        <option value="tabletop">机上演習</option>
        <option value="functional">機能演習</option>
        <option value="full_scale">実地演習</option>
        <option value="drill">訓練</option>
      </select>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>

    <table v-else class="data-table">
      <thead>
        <tr>
          <th>番号</th>
          <th>タイトル</th>
          <th>種別</th>
          <th>ステータス</th>
          <th>シナリオ</th>
          <th>参加者数</th>
          <th>予定日時</th>
          <th>完了日時</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="ex in store.exercises" :key="ex.id" @click="detailEx = ex" class="clickable">
          <td>{{ ex.exerciseNumber }}</td>
          <td>{{ ex.title }}</td>
          <td><span :class="'badge type-' + ex.type">{{ typeLabel(ex.type) }}</span></td>
          <td><span :class="'badge exst-' + ex.status">{{ statusLabel(ex.status) }}</span></td>
          <td>{{ ex.scenarioTitle ?? '—' }}</td>
          <td>{{ ex.participantsCount }}</td>
          <td>{{ formatDate(ex.scheduledAt) }}</td>
          <td>{{ ex.completedAt ? formatDate(ex.completedAt) : '—' }}</td>
        </tr>
        <tr v-if="store.exercises.length === 0">
          <td colspan="8" class="empty">演習なし</td>
        </tr>
      </tbody>
    </table>

    <!-- Detail modal -->
    <div v-if="detailEx" class="modal-overlay" @click.self="detailEx = null">
      <div class="modal">
        <h3>{{ detailEx.exerciseNumber }} — {{ detailEx.title }}</h3>
        <table class="detail-table">
          <tr><th>種別</th><td><span :class="'badge type-' + detailEx.type">{{ typeLabel(detailEx.type) }}</span></td></tr>
          <tr><th>ステータス</th><td><span :class="'badge exst-' + detailEx.status">{{ statusLabel(detailEx.status) }}</span></td></tr>
          <tr><th>シナリオ</th><td>{{ detailEx.scenarioTitle ?? '—' }}</td></tr>
          <tr><th>参加者数</th><td>{{ detailEx.participantsCount }}</td></tr>
          <tr><th>予定日時</th><td>{{ formatDate(detailEx.scheduledAt) }}</td></tr>
          <tr v-if="detailEx.completedAt"><th>完了日時</th><td>{{ formatDate(detailEx.completedAt) }}</td></tr>
          <tr><th>登録日時</th><td>{{ formatDate(detailEx.createdAt) }}</td></tr>
        </table>
        <div class="modal-actions">
          <button @click="detailEx = null">閉じる</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useExercisesStore } from '@/stores/exercises'
import type { Exercise } from '@/types'

const store = useExercisesStore()
const filterStatus = ref('')
const filterType = ref('')
const detailEx = ref<Exercise | null>(null)

function applyFilter() {
  store.fetchExercises(filterStatus.value || undefined, filterType.value || undefined)
}

function typeLabel(t: Exercise['type']) {
  const map: Record<string, string> = { tabletop: '机上', functional: '機能', full_scale: '実地', drill: '訓練' }
  return map[t] ?? t
}

function statusLabel(s: Exercise['status']) {
  const map: Record<string, string> = { planned: '計画済み', in_progress: '実施中', completed: '完了', cancelled: 'キャンセル' }
  return map[s] ?? s
}

function formatDate(d?: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => store.fetchExercises())
</script>

<style scoped>
.exercises { padding: 1rem; }
h2 { margin-bottom: 1rem; }
.filters { display: flex; gap: 0.75rem; margin-bottom: 1rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th { background: #1e1e2e; padding: 0.6rem 0.75rem; text-align: left; color: #a6adc8; font-weight: 600; }
.data-table td { padding: 0.6rem 0.75rem; border-bottom: 1px solid #313244; }
.clickable { cursor: pointer; }
.clickable:hover td { background: #1e1e2e; }
.empty { text-align: center; color: #6c7086; padding: 2rem; }
.badge { padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.78rem; font-weight: 600; }
.type-tabletop { background: #89b4fa20; color: #89b4fa; }
.type-functional { background: #cba6f720; color: #cba6f7; }
.type-full_scale { background: #f38ba820; color: #f38ba8; }
.type-drill { background: #a6e3a120; color: #a6e3a1; }
.exst-planned { background: #89b4fa20; color: #89b4fa; }
.exst-in_progress { background: #f9e2af20; color: #f9e2af; }
.exst-completed { background: #a6e3a120; color: #a6e3a1; }
.exst-cancelled { background: #a6adc820; color: #6c7086; }
.modal-overlay { position: fixed; inset: 0; background: #00000088; display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #45475a; border-radius: 8px; padding: 1.5rem; min-width: 400px; max-width: 520px; }
.modal h3 { margin-bottom: 0.75rem; }
.detail-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; margin-bottom: 1rem; }
.detail-table th { width: 130px; color: #a6adc8; padding: 0.4rem 0; text-align: left; }
.detail-table td { padding: 0.4rem 0; }
.modal-actions { display: flex; gap: 0.5rem; justify-content: flex-end; }
.error { color: #f38ba8; }
</style>
