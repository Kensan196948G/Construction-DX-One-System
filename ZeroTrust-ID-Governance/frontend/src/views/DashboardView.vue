<template>
  <div class="dashboard">
    <h2>ダッシュボード</h2>
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-value user-active">{{ activeCount }}</div>
        <div class="kpi-label">アクティブユーザー</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value user-locked">{{ lockedCount }}</div>
        <div class="kpi-label">ロックユーザー</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value">{{ userStore.users.length }}</div>
        <div class="kpi-label">総ユーザー数</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-value req-pending">{{ pendingCount }}</div>
        <div class="kpi-label">承認待ち申請</div>
      </div>
    </div>

    <h3>最近のユーザー</h3>
    <p v-if="userStore.loading">読み込み中...</p>
    <p v-else-if="userStore.error" class="error">{{ userStore.error }}</p>
    <table v-else-if="userStore.users.length" class="data-table">
      <thead>
        <tr>
          <th>ユーザー名</th>
          <th>氏名</th>
          <th>種別</th>
          <th>ステータス</th>
          <th>MFA</th>
          <th>登録日</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in recentUsers" :key="user.id">
          <td>{{ user.username }}</td>
          <td>{{ user.full_name }}</td>
          <td><span :class="['badge', 'type-' + user.user_type]">{{ user.user_type }}</span></td>
          <td><span :class="['badge', 'status-' + user.status]">{{ user.status }}</span></td>
          <td>{{ user.mfa_enabled ? '✅' : '❌' }}</td>
          <td>{{ formatDate(user.created_at) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>ユーザーはありません。</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useUsersStore } from '@/stores/users'
import { useAccessRequestsStore } from '@/stores/accessRequests'

const userStore = useUsersStore()
const reqStore = useAccessRequestsStore()

onMounted(() => {
  userStore.fetchUsers()
  reqStore.fetchRequests()
})

const activeCount = computed(() => userStore.activeUsers().length)
const lockedCount = computed(() => userStore.lockedUsers().length)
const pendingCount = computed(() => reqStore.pendingRequests().length)
const recentUsers = computed(() => userStore.users.slice(0, 10))

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ja-JP')
}
</script>

<style scoped>
.dashboard { padding: 1rem; }
.kpi-grid { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.kpi-card {
  background: #1e1e2e;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 1.25rem 2rem;
  text-align: center;
  min-width: 160px;
}
.kpi-value { font-size: 2.5rem; font-weight: bold; color: #cdd6f4; }
.kpi-value.user-active { color: #a6e3a1; }
.kpi-value.user-locked { color: #f38ba8; }
.kpi-value.req-pending { color: #fab387; }
.kpi-label { font-size: 0.85rem; color: #a6adc8; margin-top: 0.25rem; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { border: 1px solid #333; padding: 0.5rem 0.75rem; text-align: left; }
.data-table th { background: #1e1e2e; color: #a6adc8; }
.badge { padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.type-employee { background: #89b4fa; color: #1e1e2e; }
.type-contractor { background: #cba6f7; color: #1e1e2e; }
.type-partner { background: #f9e2af; color: #1e1e2e; }
.type-admin { background: #f38ba8; color: #1e1e2e; }
.status-active { background: #a6e3a1; color: #1e1e2e; }
.status-disabled { background: #6c7086; color: #cdd6f4; }
.status-locked { background: #f38ba8; color: #1e1e2e; }
.error { color: #f38ba8; }
</style>
