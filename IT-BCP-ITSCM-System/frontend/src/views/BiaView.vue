<template>
  <div class="bia">
    <div class="page-header">
      <h2>BIA 業務影響分析</h2>
      <button @click="showCreate = true">+ 新規 BIA 作成</button>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>

    <table v-else class="data-table">
      <thead>
        <tr>
          <th>システム ID</th>
          <th>評価日</th>
          <th>RTO (時間)</th>
          <th>RPO (時間)</th>
          <th>影響レベル</th>
          <th>備考</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in store.biaList" :key="item.id ?? item.system_id + item.assessment_date">
          <td>{{ item.system_id ?? item.systemId ?? '—' }}</td>
          <td>{{ item.assessment_date ?? item.assessmentDate ?? '—' }}</td>
          <td>{{ item.rto_hours ?? item.rtoHours ?? '—' }}</td>
          <td>{{ item.rpo_hours ?? item.rpoHours ?? '—' }}</td>
          <td>
            <span :class="'badge impact-' + (item.impact_level ?? item.impactLevel ?? 'unknown')">
              {{ item.impact_level ?? item.impactLevel ?? '—' }}
            </span>
          </td>
          <td>{{ item.notes ?? '—' }}</td>
        </tr>
        <tr v-if="store.biaList.length === 0">
          <td colspan="6" class="empty">BIA レコードなし</td>
        </tr>
      </tbody>
    </table>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal">
        <h3>新規 BIA 作成</h3>
        <div class="form-grid">
          <label>
            システム ID
            <input v-model="form.system_id" placeholder="例: sys-001" />
          </label>
          <label>
            評価日
            <input v-model="form.assessment_date" type="date" />
          </label>
          <label>
            RTO (時間)
            <input v-model.number="form.rto_hours" type="number" min="0" />
          </label>
          <label>
            RPO (時間)
            <input v-model.number="form.rpo_hours" type="number" min="0" />
          </label>
          <label>
            影響レベル
            <select v-model="form.impact_level">
              <option value="critical">クリティカル</option>
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </label>
          <label class="span2">
            備考
            <textarea v-model="form.notes" rows="3" placeholder="（任意）"></textarea>
          </label>
        </div>
        <p v-if="createError" class="error">{{ createError }}</p>
        <div class="modal-actions">
          <button @click="submitCreate" :disabled="creating">
            {{ creating ? '作成中...' : '作成' }}
          </button>
          <button @click="showCreate = false">キャンセル</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useBiaStore } from '@/stores/bia'
import type { BiaCreateInput } from '@/api/bia'

const store = useBiaStore()
const showCreate = ref(false)
const creating = ref(false)
const createError = ref<string | null>(null)

const defaultForm = (): BiaCreateInput => ({
  system_id: '',
  assessment_date: new Date().toISOString().slice(0, 10),
  rto_hours: 4,
  rpo_hours: 1,
  impact_level: 'medium',
  notes: '',
})

const form = ref<BiaCreateInput>(defaultForm())

async function submitCreate() {
  if (!form.value.system_id.trim()) {
    createError.value = 'システム ID を入力してください'
    return
  }
  if (!form.value.assessment_date) {
    createError.value = '評価日を入力してください'
    return
  }
  creating.value = true
  createError.value = null
  const ok = await store.createBia(form.value)
  creating.value = false
  if (ok) {
    showCreate.value = false
    form.value = defaultForm()
  } else {
    createError.value = store.error ?? 'BIA の作成に失敗しました'
  }
}

onMounted(() => store.fetchBia())
</script>

<style scoped>
.bia { padding: 1rem; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th { background: #1e1e2e; padding: 0.6rem 0.75rem; text-align: left; color: #a6adc8; font-weight: 600; }
.data-table td { padding: 0.6rem 0.75rem; border-bottom: 1px solid #313244; }
.empty { text-align: center; color: #6c7086; padding: 2rem; }
.badge { padding: 0.15rem 0.45rem; border-radius: 4px; font-size: 0.78rem; font-weight: 600; }
.impact-critical { background: #f38ba820; color: #f38ba8; }
.impact-high { background: #fab38720; color: #fab387; }
.impact-medium { background: #f9e2af20; color: #f9e2af; }
.impact-low { background: #a6e3a120; color: #a6e3a1; }
.impact-unknown { background: #6c708620; color: #6c7086; }
.modal-overlay { position: fixed; inset: 0; background: #00000088; display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #45475a; border-radius: 8px; padding: 1.5rem; min-width: 400px; max-width: 560px; }
.modal h3 { margin-bottom: 0.75rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1rem; }
.form-grid label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.85rem; color: #a6adc8; }
.span2 { grid-column: span 2; }
.modal-actions { display: flex; gap: 0.5rem; justify-content: flex-end; }
.error { color: #f38ba8; font-size: 0.85rem; margin-bottom: 0.5rem; }
</style>
