<template>
  <div class="users-view">
    <h2>ユーザー管理</h2>

    <div class="filters">
      <select v-model="filterType" @change="applyFilter">
        <option value="">種別: すべて</option>
        <option value="employee">employee</option>
        <option value="contractor">contractor</option>
        <option value="partner">partner</option>
        <option value="admin">admin</option>
      </select>
      <select v-model="filterStatus" @change="applyFilter">
        <option value="">ステータス: すべて</option>
        <option value="active">active</option>
        <option value="disabled">disabled</option>
        <option value="locked">locked</option>
      </select>
      <button @click="showModal = true">+ 新規ユーザー</button>
    </div>

    <p v-if="store.loading">読み込み中...</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>
    <table v-else-if="store.users.length" class="data-table">
      <thead>
        <tr>
          <th>ユーザー名</th>
          <th>氏名</th>
          <th>メール</th>
          <th>種別</th>
          <th>ステータス</th>
          <th>MFA</th>
          <th>リスクスコア</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in store.users" :key="user.id">
          <td>{{ user.username }}</td>
          <td>{{ user.full_name }}</td>
          <td>{{ user.email }}</td>
          <td><span :class="['badge', 'type-' + user.user_type]">{{ user.user_type }}</span></td>
          <td>
            <select
              :value="user.status"
              @change="(e) => changeStatus(user.id, (e.target as HTMLSelectElement).value as UserStatus)"
            >
              <option value="active">active</option>
              <option value="disabled">disabled</option>
              <option value="locked">locked</option>
            </select>
          </td>
          <td>{{ user.mfa_enabled ? '✅' : '❌' }}</td>
          <td>{{ user.risk_score }}</td>
          <td>
            <button class="btn-sm" @click="changeStatus(user.id, 'locked')" v-if="user.status === 'active'">ロック</button>
            <button class="btn-sm btn-ok" @click="changeStatus(user.id, 'active')" v-if="user.status === 'locked'">解除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else>ユーザーはありません。</p>

    <!-- 新規ユーザー登録モーダル -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>新規ユーザー登録</h3>
        <div class="form-group">
          <label>ユーザー名</label>
          <input v-model="form.username" placeholder="username" />
        </div>
        <div class="form-group">
          <label>氏名</label>
          <input v-model="form.full_name" placeholder="山田 太郎" />
        </div>
        <div class="form-group">
          <label>メール</label>
          <input v-model="form.email" type="email" placeholder="user@example.com" />
        </div>
        <div class="form-group">
          <label>種別</label>
          <select v-model="form.user_type">
            <option value="employee">employee</option>
            <option value="contractor">contractor</option>
            <option value="partner">partner</option>
            <option value="admin">admin</option>
          </select>
        </div>
        <div class="form-group">
          <label>部署</label>
          <input v-model="form.department" placeholder="情報システム部" />
        </div>
        <div class="modal-actions">
          <button @click="submitUser">登録</button>
          <button @click="showModal = false">キャンセル</button>
        </div>
        <p v-if="store.error" class="error">{{ store.error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUsersStore } from '@/stores/users'
import type { UserType, UserStatus } from '@/types'

const store = useUsersStore()
const filterType = ref('')
const filterStatus = ref('')
const showModal = ref(false)
const form = ref({ username: '', full_name: '', email: '', user_type: 'employee' as UserType, department: '' })

onMounted(() => store.fetchUsers())

function applyFilter() {
  store.fetchUsers(
    filterType.value as UserType || undefined,
    filterStatus.value as UserStatus || undefined,
  )
}

async function changeStatus(id: string, status: UserStatus) {
  await store.updateUserStatus(id, status)
}

async function submitUser() {
  const result = await store.createUser({
    ...form.value,
    department: form.value.department || null,
  })
  if (result) {
    showModal.value = false
    form.value = { username: '', full_name: '', email: '', user_type: 'employee', department: '' }
  }
}
</script>

<style scoped>
.users-view { padding: 1rem; }
.filters { display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.type-employee { background: #89b4fa; color: #1e1e2e; }
.type-contractor { background: #cba6f7; color: #1e1e2e; }
.type-partner { background: #f9e2af; color: #1e1e2e; }
.type-admin { background: #f38ba8; color: #1e1e2e; }
.btn-sm { font-size: 0.75rem; padding: 0.2rem 0.5rem; }
.btn-ok { background: #40a02b; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #1e1e2e; border: 1px solid #333; border-radius: 8px; padding: 1.5rem; min-width: 360px; }
.modal h3 { margin-bottom: 1rem; }
.form-group { display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem; }
.form-group label { font-size: 0.85rem; color: #a6adc8; }
.modal-actions { display: flex; gap: 0.5rem; margin-top: 1rem; }
.error { color: #f38ba8; margin-top: 0.5rem; }
</style>
