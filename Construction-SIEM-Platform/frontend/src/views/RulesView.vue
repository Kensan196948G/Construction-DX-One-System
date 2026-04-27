<template>
  <div class="rules-view">
    <h2>検知ルール管理</h2>

    <!-- Stats Summary -->
    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-label">ルール総数</span>
        <span class="stat-value">{{ rules.length }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">アクティブ</span>
        <span class="stat-value active">{{ stats?.total_active ?? '-' }}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">非アクティブ</span>
        <span class="stat-value inactive">{{ stats?.total_inactive ?? '-' }}</span>
      </div>
      <div v-if="stats?.by_severity" v-for="(count, sev) in stats.by_severity" :key="sev" class="stat-card">
        <span class="stat-label">{{ sev }}</span>
        <span :class="['stat-value', 'sev-' + sev]">{{ count }}</span>
      </div>
    </div>

    <!-- Toolbar / Filters -->
    <div class="toolbar">
      <label>
        重大度:
        <select v-model="filters.severity" @change="loadRules">
          <option value="">すべて</option>
          <option value="critical">critical</option>
          <option value="high">high</option>
          <option value="medium">medium</option>
          <option value="low">low</option>
        </select>
      </label>
      <label>
        カテゴリ:
        <input v-model="filters.category" placeholder="カテゴリ" @input="loadRules" />
      </label>
      <label>
        ルールタイプ:
        <select v-model="filters.rule_type" @change="loadRules">
          <option value="">すべて</option>
          <option value="sigma">sigma</option>
          <option value="yara">yara</option>
          <option value="custom">custom</option>
        </select>
      </label>
      <label>
        状態:
        <select v-model="filters.is_active" @change="loadRules">
          <option :value="''">すべて</option>
          <option :value="true">アクティブ</option>
          <option :value="false">非アクティブ</option>
        </select>
      </label>
      <button @click="loadRules">更新</button>
      <button class="btn-primary" @click="openCreate">＋ 新規ルール</button>
    </div>

    <p v-if="loading">読み込み中...</p>
    <p v-else-if="error" class="error">{{ error }}</p>

    <!-- Rule Table -->
    <table v-else-if="rules.length" class="data-table">
      <thead>
        <tr>
          <th>ルールID</th>
          <th>名前</th>
          <th>重大度</th>
          <th>タイプ</th>
          <th>カテゴリ</th>
          <th>ステータス</th>
          <th>一致回数</th>
          <th>最終一致</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rule in rules" :key="rule.id">
          <td class="mono">{{ rule.rule_id }}</td>
          <td>
            <a class="rule-name-link" @click="openDetail(rule)">{{ rule.name }}</a>
          </td>
          <td><span :class="['badge', 'sev-' + rule.severity]">{{ rule.severity }}</span></td>
          <td><span :class="['badge', 'type-' + rule.rule_type]">{{ rule.rule_type }}</span></td>
          <td>{{ rule.category }}</td>
          <td>
            <label class="toggle-switch">
              <input type="checkbox" :checked="rule.is_active" @change="onToggle(rule.id)" />
              <span class="toggle-slider"></span>
            </label>
          </td>
          <td>{{ rule.match_count }}</td>
          <td>{{ rule.last_matched_at ? formatDate(rule.last_matched_at) : '-' }}</td>
          <td class="actions-cell">
            <button @click="openEdit(rule)" title="編集">✏️</button>
            <button @click="openTest(rule)" title="テスト">🧪</button>
            <button @click="confirmDelete(rule)" title="削除">🗑️</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>ルールはありません。</p>

    <!-- Create / Edit Modal -->
    <div v-if="showFormModal" class="modal-overlay" @click.self="showFormModal = false">
      <div class="modal modal-wide">
        <h3>{{ editingRule ? 'ルール編集' : '新規ルール登録' }}</h3>
        <form @submit.prevent="submitForm">
          <label>ルール名: <input v-model="form.name" required /></label>
          <label>説明: <textarea v-model="form.description" rows="2"></textarea></label>
          <div class="form-row">
            <label>
              ルールタイプ:
              <select v-model="form.rule_type">
                <option value="sigma">sigma</option>
                <option value="yara">yara</option>
                <option value="custom">custom</option>
              </select>
            </label>
            <label>
              重大度:
              <select v-model="form.severity">
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
                <option value="critical">critical</option>
              </select>
            </label>
            <label>
              カテゴリ:
              <input v-model="form.category" placeholder="例: malware, network" />
            </label>
          </div>
          <label>
            MITRE ATT&CK ID:
            <input v-model="form.mitre_attack_id" placeholder="例: T1055" />
          </label>
          <label>
            ルール内容 (コード):
            <textarea v-model="form.rule_content" class="code-textarea" rows="10" spellcheck="false"></textarea>
          </label>
          <div class="modal-actions">
            <button type="submit">{{ editingRule ? '更新' : '登録' }}</button>
            <button type="button" @click="showFormModal = false">キャンセル</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="detailRule" class="modal-overlay" @click.self="detailRule = null">
      <div class="modal modal-wide">
        <h3>{{ detailRule.name }}</h3>
        <div class="detail-grid">
          <div><strong>ルールID:</strong> <span class="mono">{{ detailRule.rule_id }}</span></div>
          <div><strong>タイプ:</strong> <span :class="['badge', 'type-' + detailRule.rule_type]">{{ detailRule.rule_type }}</span></div>
          <div><strong>重大度:</strong> <span :class="['badge', 'sev-' + detailRule.severity]">{{ detailRule.severity }}</span></div>
          <div><strong>カテゴリ:</strong> {{ detailRule.category }}</div>
          <div><strong>ステータス:</strong> {{ detailRule.is_active ? 'アクティブ' : '非アクティブ' }}</div>
          <div><strong>一致回数:</strong> {{ detailRule.match_count }}</div>
          <div><strong>最終一致:</strong> {{ detailRule.last_matched_at ? formatDate(detailRule.last_matched_at) : '-' }}</div>
          <div><strong>MITRE ATT&CK:</strong> {{ detailRule.mitre_attack_id ?? '-' }}</div>
          <div><strong>作成日:</strong> {{ formatDate(detailRule.created_at) }}</div>
          <div><strong>更新日:</strong> {{ formatDate(detailRule.updated_at) }}</div>
          <div v-if="detailRule.description" class="detail-fullwidth"><strong>説明:</strong> {{ detailRule.description }}</div>
          <div class="detail-fullwidth">
            <strong>ルール内容:</strong>
            <pre class="code-block">{{ detailRule.rule_content }}</pre>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="detailRule = null">閉じる</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal">
        <h3>削除の確認</h3>
        <p>ルール「{{ deleteTarget.name }}」({{ deleteTarget.rule_id }}) を削除してもよろしいですか？</p>
        <div class="modal-actions">
          <button class="btn-danger" @click="doDelete">削除</button>
          <button @click="deleteTarget = null">キャンセル</button>
        </div>
      </div>
    </div>

    <!-- Test Rule Modal -->
    <div v-if="showTestModal" class="modal-overlay" @click.self="closeTest">
      <div class="modal modal-wide">
        <h3>ルールテスト</h3>
        <form @submit.prevent="doTest">
          <label>
            テスト対象ルール:
            <select v-model="testForm.ruleId">
              <option value="">カスタム内容を使用</option>
              <option v-for="r in rules" :key="r.id" :value="r.id">{{ r.name }} ({{ r.rule_id }})</option>
            </select>
          </label>
          <label>
            ルールタイプ:
            <select v-model="testForm.rule_type">
              <option value="sigma">sigma</option>
              <option value="yara">yara</option>
              <option value="custom">custom</option>
            </select>
          </label>
          <label>
            ルール内容:
            <textarea v-model="testForm.rule_content" class="code-textarea" rows="6" spellcheck="false"></textarea>
          </label>
          <label>
            イベントデータ (JSON):
            <textarea v-model="testForm.eventDataStr" class="code-textarea" rows="6" spellcheck="false" placeholder='{"field": "value"}'></textarea>
          </label>
          <div v-if="testJsonError" class="error">{{ testJsonError }}</div>
          <div class="modal-actions">
            <button type="submit" :disabled="testing">テスト実行</button>
            <button type="button" @click="closeTest">閉じる</button>
          </div>
        </form>
        <div v-if="testResult" class="test-result">
          <p :class="testResult.matched ? 'matched' : 'unmatched'">
            {{ testResult.matched ? '✓ 一致しました' : '✗ 一致しませんでした' }}
          </p>
          <pre v-if="testResult.details" class="code-block">{{ testResult.details }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRulesStore } from '@/stores/rules'
import type { Rule, RuleCreate, RuleUpdate, RuleType, RuleSeverity } from '@/types'

const store = useRulesStore()
const rules = computed(() => store.rules)
const loading = computed(() => store.loading)
const error = computed(() => store.error)
const stats = computed(() => store.stats)
const filters = computed(() => store.filters)

const showFormModal = ref(false)
const editingRule = ref<Rule | null>(null)

const form = ref<RuleCreate>({
  name: '',
  description: '',
  rule_type: 'sigma',
  rule_content: '',
  severity: 'medium',
  category: '',
  mitre_attack_id: '',
})

const detailRule = ref<Rule | null>(null)
const deleteTarget = ref<Rule | null>(null)

const showTestModal = ref(false)
const testing = ref(false)
const testForm = ref({
  ruleId: '',
  rule_type: 'sigma' as RuleType,
  rule_content: '',
  eventDataStr: '{}',
})
const testJsonError = ref('')
const testResult = ref<{ matched: boolean; details: string | null } | null>(null)

async function loadRules() {
  await store.fetchRules()
  await store.fetchStats()
}

function openCreate() {
  editingRule.value = null
  form.value = {
    name: '',
    description: '',
    rule_type: 'sigma',
    rule_content: '',
    severity: 'medium',
    category: '',
    mitre_attack_id: '',
  }
  showFormModal.value = true
}

function openEdit(rule: Rule) {
  editingRule.value = rule
  form.value = {
    name: rule.name,
    description: rule.description ?? '',
    rule_type: rule.rule_type,
    rule_content: rule.rule_content,
    severity: rule.severity,
    category: rule.category,
    mitre_attack_id: rule.mitre_attack_id ?? '',
  }
  showFormModal.value = true
}

async function submitForm() {
  const data: RuleCreate = {
    name: form.value.name,
    description: form.value.description || null,
    rule_type: form.value.rule_type,
    rule_content: form.value.rule_content,
    severity: form.value.severity,
    category: form.value.category,
    mitre_attack_id: form.value.mitre_attack_id || null,
  }
  let ok = false
  if (editingRule.value) {
    const result = await store.updateRule(editingRule.value.id, data as RuleUpdate)
    ok = !!result
  } else {
    const result = await store.createRule(data)
    ok = !!result
  }
  if (ok) {
    showFormModal.value = false
    await store.fetchStats()
  }
}

function openDetail(rule: Rule) {
  detailRule.value = rule
}

function confirmDelete(rule: Rule) {
  deleteTarget.value = rule
}

async function doDelete() {
  if (!deleteTarget.value) return
  const ok = await store.deleteRule(deleteTarget.value.id)
  if (ok) {
    deleteTarget.value = null
    await store.fetchStats()
  }
}

async function onToggle(id: string) {
  await store.toggleRule(id)
  await store.fetchStats()
}

function openTest(rule?: Rule) {
  testForm.value = {
    ruleId: rule?.id ?? '',
    rule_type: rule?.rule_type ?? 'sigma',
    rule_content: rule?.rule_content ?? '',
    eventDataStr: '{}',
  }
  testResult.value = null
  testJsonError.value = ''
  showTestModal.value = true
}

function closeTest() {
  showTestModal.value = false
  testResult.value = null
  store.clearTestResult()
}

async function doTest() {
  testJsonError.value = ''
  let eventData: Record<string, unknown>
  try {
    eventData = JSON.parse(testForm.value.eventDataStr)
  } catch {
    testJsonError.value = 'イベントデータが有効なJSONではありません'
    return
  }
  testing.value = true
  try {
    const result = await store.testRule({
      rule_content: testForm.value.rule_content,
      rule_type: testForm.value.rule_type,
      event_data: eventData,
    })
    testResult.value = result
  } finally {
    testing.value = false
  }
}

watch(() => testForm.value.ruleId, (id) => {
  if (id) {
    const rule = rules.value.find((r) => r.id === id)
    if (rule) {
      testForm.value.rule_type = rule.rule_type
      testForm.value.rule_content = rule.rule_content
    }
  }
})

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}

onMounted(loadRules)
</script>

<style scoped>
.rules-view { padding: 1rem; }

.stats-row { display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
.stat-card {
  background: #1e1e2e; border: 1px solid #313244; border-radius: 8px;
  padding: 0.75rem 1rem; min-width: 120px; text-align: center;
}
.stat-label { display: block; font-size: 0.75rem; color: #6c7086; margin-bottom: 0.25rem; }
.stat-value { font-size: 1.3rem; font-weight: 700; }
.stat-value.active { color: #a6e3a1; }
.stat-value.inactive { color: #6c7086; }

.toolbar { display: flex; gap: 0.75rem; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; }
.btn-primary { background: #89b4fa; color: #1e1e2e; border: none; font-weight: 600; }
.btn-primary:hover { background: #74c7ec; }
.btn-danger { background: #f38ba8; color: #1e1e2e; border: none; font-weight: 600; }
.btn-danger:hover { background: #eba0ac; }

.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.4rem 0.6rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; white-space: nowrap; }

.rule-name-link { color: #89b4fa; cursor: pointer; text-decoration: underline; }
.rule-name-link:hover { color: #74c7ec; }

.mono { font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 0.8rem; }

.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.sev-critical { background: #f38ba8; color: #1e1e2e; }
.sev-high { background: #fab387; color: #1e1e2e; }
.sev-medium { background: #f9e2af; color: #1e1e2e; }
.sev-low { background: #a6e3a1; color: #1e1e2e; }
.type-sigma { background: #89b4fa; color: #1e1e2e; }
.type-yara { background: #cba6f7; color: #1e1e2e; }
.type-custom { background: #6c7086; color: #cdd6f4; }

.toggle-switch { position: relative; display: inline-block; width: 40px; height: 22px; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute; cursor: pointer; inset: 0;
  background: #45475a; border-radius: 22px; transition: 0.2s;
}
.toggle-slider::before {
  content: ''; position: absolute; height: 16px; width: 16px; left: 3px; bottom: 3px;
  background: #cdd6f4; border-radius: 50%; transition: 0.2s;
}
.toggle-switch input:checked + .toggle-slider { background: #a6e3a1; }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(18px); background: #1e1e2e; }

.actions-cell { white-space: nowrap; }
.actions-cell button { background: transparent; border: none; cursor: pointer; font-size: 1rem; padding: 0.15rem 0.3rem; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal {
  background: #1e1e2e; border: 1px solid #45475a; border-radius: 8px;
  padding: 1.5rem; min-width: 400px; max-height: 90vh; overflow-y: auto;
}
.modal-wide { min-width: 600px; }
.modal h3 { margin-top: 0; margin-bottom: 1rem; }
.modal label { display: block; margin-bottom: 0.75rem; }
.modal input, .modal select, .modal textarea {
  display: block; width: 100%; margin-top: 0.25rem;
  background: #313244; border: 1px solid #45475a; color: #cdd6f4;
  padding: 0.4rem; border-radius: 4px;
}
.modal-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }

.form-row { display: flex; gap: 0.75rem; }
.form-row label { flex: 1; }

.code-textarea { font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 0.8rem; line-height: 1.4; tab-size: 2; }

.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem 1rem; }
.detail-fullwidth { grid-column: 1 / -1; }
.detail-grid strong { color: #a6adc8; }

.code-block {
  background: #11111b; border: 1px solid #313244; border-radius: 4px;
  padding: 0.75rem; font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.8rem; overflow-x: auto; white-space: pre-wrap; margin-top: 0.25rem;
}

.test-result { margin-top: 1rem; padding: 1rem; border-radius: 6px; border: 1px solid #45475a; }
.test-result .matched { color: #a6e3a1; font-weight: 700; }
.test-result .unmatched { color: #f38ba8; font-weight: 700; }

.error { color: #f38ba8; }
</style>
