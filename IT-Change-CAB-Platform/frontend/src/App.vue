<template>
  <div id="app-layout">
    <nav class="sidebar">
      <div class="sidebar-title">
        <span class="icon">🔄</span>
        <span>CAB</span>
      </div>
      <ul>
        <li><RouterLink to="/">📊 ダッシュボード</RouterLink></li>
        <li><RouterLink to="/rfcs">📝 RFC管理</RouterLink></li>
        <li><RouterLink to="/cab">🏛️ CAB会議</RouterLink></li>
      </ul>
      <div class="health-dot">
        API: <span :class="'dot dot-' + healthStatus">●</span>
      </div>
    </nav>
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { healthApi } from '@/api/health'

const healthStatus = ref<'ok' | 'error' | 'unknown'>('unknown')

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
  width: 200px; background: #1e1e2e; border-right: 1px solid #313244;
  padding: 1rem; display: flex; flex-direction: column; gap: 1rem;
}
.sidebar-title { font-size: 1.1rem; font-weight: bold; display: flex; align-items: center; gap: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px solid #313244; }
.sidebar ul { list-style: none; display: flex; flex-direction: column; gap: 0.25rem; }
.sidebar a { display: block; padding: 0.5rem; border-radius: 4px; text-decoration: none; color: #cdd6f4; }
.sidebar a:hover, .sidebar a.router-link-active { background: #313244; }
.health-dot { margin-top: auto; font-size: 0.8rem; color: #6c7086; }
.dot { font-size: 1rem; }
.dot-ok { color: #a6e3a1; }
.dot-error { color: #f38ba8; }
.dot-unknown { color: #6c7086; }
.main-content { flex: 1; overflow: auto; padding: 1rem; }
</style>
