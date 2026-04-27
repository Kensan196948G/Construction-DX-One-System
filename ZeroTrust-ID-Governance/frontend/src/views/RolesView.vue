<template>
  <div class="roles-view">
    <h2>ロール管理</h2>

    <div class="filters">
      <input v-model="searchQuery" placeholder="ロール名で検索..." @input="applyFilter" />
      <button @click="openCreateModal">+ 新規ロール</button>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>
    <table v-else-if="filteredRoles.length" class="data-table">
      <thead>
        <tr>
          <th>ロール名</th>
          <th>説明</th>
          <th>権限</th>
          <th>種別</th>
          <th>作成日</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="role in filteredRoles" :key="role.id" :class="{ 'row-selected': selectedRoleId === role.id }">
          <td class="role-name" @click="toggleDetail(role.id)">{{ role.name }}</td>
          <td>{{ role.description || '-' }}</td>
          <td>
            <span v-for="perm in role.permissions" :key="perm" :class="['perm-tag', permTagClass(perm)]">{{ perm }}</span>
            <span v-if="!role.permissions.length" class="no-perms">なし</span>
          </td>
          <td>
            <span v-if="role.is_privileged" class="badge badge-privileged">特権</span>
            <span v-else class="badge badge-regular">通常</span>
          </td>
          <td>{{ formatDate(role.created_at) }}</td>
          <td class="actions">
            <button class="btn-sm" @click="openDetail(role)">詳細</button>
            <button class="btn-sm" @click="openEditModal(role)">編集</button>
            <button class="btn-sm btn-danger" @click="confirmDelete(role)">削除</button>
          </td>
        </tr>
        <tr v-if="expandedRoleId" class="detail-row">
          <td colspan="6">
            <div class="role-detail">
              <div class="detail-section">
                <h4>{{ expandedRole?.name }} の詳細</h4>
                <p><strong>説明:</strong> {{ expandedRole?.description || '-' }}</p>
                <p><strong>権限:</strong>
                  <span v-for="perm in expandedRole?.permissions" :key="perm" :class="['perm-tag', permTagClass(perm)]">{{ perm }}</span>
                  <span v-if="!expandedRole?.permissions.length" class="no-perms">なし</span>
                </p>
                <p><strong>種別:</strong>
                  <span v-if="expandedRole?.is_privileged" class="badge badge-privileged">特権</span>
                  <span v-else class="badge badge-regular">通常</span>
                </p>
                <p><strong>作成日:</strong> {{ formatDate(expandedRole?.created_at) }}</p>
              </div>

              <div class="detail-section">
                <h4>割り当てユーザー</h4>
                <div v-if="getAssignedUsers(expandedRoleId).length" class="assignee-list">
                  <div v-for="u in getAssignedUsers(expandedRoleId)" :key="u.id" class="assignee-item">
                    <span>{{ u.username }} ({{ u.full_name }})</span>
                    <button class="btn-sm btn-danger" @click="handleRevoke(expandedRoleId, u.id)">解除</button>
                  </div>
                </div>
                <p v-else class="no-data">割り当てユーザーはありません</p>
                <button class="btn-sm" @click="openAssignModal(expandedRoleId)">+ ユーザー割り当て</button>
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>ロールはありません。</p>

    <!-- Create/Edit Modal -->
    <div v-if="showFormModal" class="modal-overlay" @click.self="closeFormModal">
      <div class="modal">
        <h3>{{ isEditing ? 'ロール編集' : '新規ロール作成' }}</h3>
        <div class="form-group">
          <label>ロール名 <span class="required">*</span></label>
          <input v-model="form.name" placeholder="admin" />
        </div>
        <div class="form-group">
          <label>説明</label>
          <textarea v-model="form.description" placeholder="ロールの説明" rows="2"></textarea>
        </div>
        <div class="form-group">
          <label>権限（カンマ区切り）</label>
          <input v-model="form.permissionsInput" placeholder="read, write, delete" />
          <div v-if="parsedPermissions.length" class="perm-preview">
            <span v-for="p in parsedPermissions" :key="p" :class="['perm-tag', permTagClass(p)]">{{ p }}</span>
          </div>
        </div>
        <div class="form-group toggle-group">
          <label>
            <input type="checkbox" v-model="form.is_privileged" />
            特権ロール
          </label>
        </div>
        <div class="modal-actions">
          <button @click="submitRole">{{ isEditing ? '更新' : '作成' }}</button>
          <button @click="closeFormModal">キャンセル</button>
        </div>
        <p v-if="store.error" class="error">{{ store.error }}</p>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal modal-sm">
        <h3>ロール削除</h3>
        <p>「{{ deletingRole?.name }}」を削除してもよろしいですか？</p>
        <div class="modal-actions">
          <button class="btn-danger" @click="handleDelete">削除</button>
          <button @click="showDeleteModal = false">キャンセル</button>
        </div>
      </div>
    </div>

    <!-- Assign Modal -->
    <div v-if="showAssignModal" class="modal-overlay" @click.self="showAssignModal = false">
      <div class="modal">
        <h3>ユーザー割り当て</h3>
        <p class="assign-role-label">ロール: <strong>{{ assigningRoleName }}</strong></p>
        <div class="form-group">
          <label>ユーザー</label>
          <select v-model="assignForm.userId">
            <option value="" disabled>ユーザーを選択</option>
            <option v-for="u in availableUsers" :key="u.id" :value="u.id">{{ u.username }} ({{ u.full_name }})</option>
          </select>
        </div>
        <div class="form-group">
          <label>有効期限（任意）</label>
          <input v-model="assignForm.expiresAt" type="datetime-local" />
        </div>
        <div class="modal-actions">
          <button @click="handleAssign" :disabled="!assignForm.userId">割り当て</button>
          <button @click="showAssignModal = false">キャンセル</button>
        </div>
        <p v-if="store.error" class="error">{{ store.error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRolesStore } from '@/stores/roles'
import { useUsersStore } from '@/stores/users'
import type { Role } from '@/types'

const store = useRolesStore()
const userStore = useUsersStore()

const searchQuery = ref('')
const showFormModal = ref(false)
const isEditing = ref(false)
const editingId = ref<string | null>(null)
const showDeleteModal = ref(false)
const deletingRole = ref<Role | null>(null)
const showAssignModal = ref(false)
const assigningRoleId = ref('')
const assigningRoleName = ref('')
const selectedRoleId = ref('')
const expandedRoleId = ref('')

const form = ref({
  name: '',
  description: '',
  permissionsInput: '',
  is_privileged: false,
})

const assignForm = ref({
  userId: '',
  expiresAt: '',
})

const availableUsers = computed(() => userStore.users)

const parsedPermissions = computed(() =>
  form.value.permissionsInput
    .split(',')
    .map((p) => p.trim())
    .filter(Boolean),
)

const filteredRoles = computed(() => {
  if (!searchQuery.value) return store.roles
  const q = searchQuery.value.toLowerCase()
  return store.roles.filter((r) => r.name.toLowerCase().includes(q))
})

const expandedRole = computed(() => store.roles.find((r) => r.id === expandedRoleId.value) || null)

onMounted(async () => {
  await Promise.all([store.fetchRoles(), userStore.fetchUsers()])
})

function applyFilter() {}

function permTagClass(perm: string): string {
  const lower = perm.toLowerCase()
  if (lower.includes('read') || lower.includes('view')) return 'perm-read'
  if (lower.includes('write') || lower.includes('create') || lower.includes('edit')) return 'perm-write'
  if (lower.includes('delete') || lower.includes('remove')) return 'perm-delete'
  if (lower.includes('admin') || lower.includes('manage')) return 'perm-admin'
  return 'perm-default'
}

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function resetForm() {
  form.value = { name: '', description: '', permissionsInput: '', is_privileged: false }
}

function openCreateModal() {
  isEditing.value = false
  editingId.value = null
  resetForm()
  store.error = null
  showFormModal.value = true
}

function openEditModal(role: Role) {
  isEditing.value = true
  editingId.value = role.id
  form.value = {
    name: role.name,
    description: role.description || '',
    permissionsInput: role.permissions.join(', '),
    is_privileged: role.is_privileged,
  }
  store.error = null
  showFormModal.value = true
}

function closeFormModal() {
  showFormModal.value = false
}

async function submitRole() {
  const data = {
    name: form.value.name,
    description: form.value.description || null,
    permissions: parsedPermissions.value,
    is_privileged: form.value.is_privileged,
  }
  if (isEditing.value && editingId.value) {
    const result = await store.updateRole(editingId.value, data)
    if (result) closeFormModal()
  } else {
    const result = await store.createRole(data)
    if (result) closeFormModal()
  }
}

function confirmDelete(role: Role) {
  deletingRole.value = role
  store.error = null
  showDeleteModal.value = true
}

async function handleDelete() {
  if (!deletingRole.value) return
  const ok = await store.deleteRole(deletingRole.value.id)
  if (ok) showDeleteModal.value = false
}

function toggleDetail(roleId: string) {
  if (expandedRoleId.value === roleId) {
    expandedRoleId.value = ''
    selectedRoleId.value = ''
  } else {
    expandedRoleId.value = roleId
    selectedRoleId.value = roleId
  }
}

function openDetail(role: Role) {
  selectedRoleId.value = role.id
  expandedRoleId.value = expandedRoleId.value === role.id ? '' : role.id
}

function openAssignModal(roleId: string) {
  const role = store.roles.find((r) => r.id === roleId)
  if (!role) return
  assigningRoleId.value = roleId
  assigningRoleName.value = role.name
  assignForm.value = { userId: '', expiresAt: '' }
  store.error = null
  showAssignModal.value = true
}

async function handleAssign() {
  if (!assignForm.value.userId) return
  const data = {
    user_id: assignForm.value.userId,
    expires_at: assignForm.value.expiresAt ? new Date(assignForm.value.expiresAt).toISOString() : null,
  }
  const result = await store.assignRole(assigningRoleId.value, data)
  if (result) showAssignModal.value = false
}

async function handleRevoke(roleId: string, userId: string) {
  await store.revokeRole(roleId, userId)
}

function getAssignedUsers(roleId: string) {
  const ids = store.assignedUserIds.get(roleId) || []
  return userStore.users.filter((u) => ids.includes(u.id))
}
</script>

<style scoped>
.roles-view { padding: 1rem; }
.filters { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; align-items: center; }
.filters input { flex: 1; min-width: 200px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.row-selected { background: #1e1e2e; }
.role-name { font-weight: 600; cursor: pointer; color: #89b4fa; }
.role-name:hover { text-decoration: underline; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.badge-privileged { background: #f38ba8; color: #1e1e2e; }
.badge-regular { background: #585b70; color: #cdd6f4; }
.perm-tag { display: inline-block; padding: 0.15rem 0.4rem; border-radius: 3px; font-size: 0.7rem; font-weight: 600; margin: 0.1rem; }
.perm-read { background: #89b4fa; color: #1e1e2e; }
.perm-write { background: #a6e3a1; color: #1e1e2e; }
.perm-delete { background: #f38ba8; color: #1e1e2e; }
.perm-admin { background: #cba6f7; color: #1e1e2e; }
.perm-default { background: #585b70; color: #cdd6f4; }
.no-perms { color: #6c7086; font-size: 0.8rem; }
.btn-sm { font-size: 0.75rem; padding: 0.2rem 0.5rem; }
.btn-danger { background: #f38ba8; color: #1e1e2e; border-color: #f38ba8; }
.btn-danger:hover { background: #e64553; }
.actions { display: flex; gap: 0.25rem; }
.detail-row td { padding: 0; }
.role-detail { padding: 1rem; background: #1e1e2e; border-top: 1px solid #313244; }
.detail-section { margin-bottom: 1rem; }
.detail-section:last-child { margin-bottom: 0; }
.detail-section h4 { margin-bottom: 0.5rem; color: #a6adc8; font-size: 0.95rem; }
.detail-section p { margin-bottom: 0.35rem; font-size: 0.85rem; }
.detail-section strong { color: #a6adc8; }
.assignee-list { margin-bottom: 0.5rem; }
.assignee-item { display: flex; align-items: center; justify-content: space-between; padding: 0.35rem 0.5rem; border-bottom: 1px solid #313244; font-size: 0.85rem; }
.assignee-item:last-child { border-bottom: none; }
.no-data { color: #6c7086; font-size: 0.85rem; font-style: italic; margin-bottom: 0.5rem; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #333; border-radius: 8px; padding: 1.5rem; min-width: 400px; max-width: 500px; }
.modal-sm { min-width: 320px; }
.modal h3 { margin-bottom: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem; }
.form-group label { font-size: 0.85rem; color: #a6adc8; }
.toggle-group label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }
.required { color: #f38ba8; }
.perm-preview { display: flex; gap: 0.25rem; flex-wrap: wrap; margin-top: 0.3rem; }
.modal-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.assign-role-label { margin-bottom: 0.75rem; font-size: 0.9rem; color: #a6adc8; }
.error { color: #f38ba8; margin-top: 0.5rem; }
</style>
