<template>
  <div id="app-layout">
    <nav v-if="auth.isAuthenticated" class="sidebar">
      <div class="sidebar-title">
        <span class="icon">🛡️</span>
        <span>BCP/ITSCM</span>
      </div>
      <ul>
        <li><RouterLink to="/">📊 ダッシュボード</RouterLink></li>
        <li><RouterLink to="/incidents">🚨 インシデント</RouterLink></li>
        <li><RouterLink to="/systems">🖥️ ITシステム</RouterLink></li>
        <li><RouterLink to="/exercises">🎯 BCP演習</RouterLink></li>
        <li><RouterLink to="/bia">📊 BIA 業務影響分析</RouterLink></li>
        <li><RouterLink to="/reports">📄 レポート</RouterLink></li>
      </ul>
      <div class="sidebar-footer">
        <div v-if="auth.user" class="user-info">
          <span class="user-name">{{ auth.user.displayName ?? auth.user.username }}</span>
        </div>
        <div class="health-dot">
          API: <span :class="'dot dot-' + healthStatus">●</span>
        </div>
        <button class="logout-btn" @click="handleLogout">ログアウト</button>
      </div>
    </nav>
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { RouterLink, RouterView } from 'vue-router'
import { healthApi } from '@/api/health'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const healthStatus = ref<'ok' | 'error' | 'unknown'>('unknown')

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

onMounted(async () => {
  try {
    const res = await healthApi.check()
    healthStatus.value = res.status === 'ok' ? 'ok' : 'error'
  } catch {
    healthStatus.value = 'error'
  }
})
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #181825; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
button {
  background: #313244; color: #cdd6f4; border: 1px solid #45475a;
  padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer;
}
button:hover { background: #45475a; }
select, input, textarea {
  background: #313244; color: #cdd6f4; border: 1px solid #45475a;
  padding: 0.3rem 0.5rem; border-radius: 4px;
}
</style>

<style scoped>
#app-layout { display: flex; min-height: 100vh; }
.sidebar {
  width: 210px; background: #1e1e2e; border-right: 1px solid #313244;
  padding: 1rem; display: flex; flex-direction: column; gap: 1rem;
}
.sidebar-title { font-size: 1.1rem; font-weight: bold; display: flex; align-items: center; gap: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid #313244; }
.sidebar ul { list-style: none; display: flex; flex-direction: column; gap: 0.25rem; }
.sidebar a { display: block; padding: 0.5rem; border-radius: 4px; text-decoration: none; color: #cdd6f4; }
.sidebar a:hover, .sidebar a.router-link-active { background: #313244; }
.sidebar-footer { margin-top: auto; display: flex; flex-direction: column; gap: 0.5rem; }
.user-info { font-size: 0.85rem; color: #a6adc8; }
.user-name { font-weight: 600; color: #cdd6f4; }
.health-dot { font-size: 0.8rem; color: #6c7086; }
.dot { font-size: 1rem; }
.dot-ok { color: #a6e3a1; }
.dot-error { color: #f38ba8; }
.dot-unknown { color: #6c7086; }
.logout-btn { font-size: 0.8rem; }
.main-content { flex: 1; overflow: auto; padding: 1rem; }
</style>
