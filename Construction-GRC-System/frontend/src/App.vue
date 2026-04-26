<template>
  <div id="app">
    <nav class="sidebar">
      <div class="logo">
        <span class="logo-icon">🏗️</span>
        <span class="logo-text">GRC</span>
      </div>
      <ul class="nav-links">
        <li>
          <router-link to="/" :class="{ active: $route.path === '/' }">
            <span class="nav-icon">📊</span>
            <span>ダッシュボード</span>
          </router-link>
        </li>
        <li>
          <router-link to="/risks" :class="{ active: $route.path.startsWith('/risks') }">
            <span class="nav-icon">⚠️</span>
            <span>リスク管理</span>
          </router-link>
        </li>
        <li>
          <router-link to="/compliance" :class="{ active: $route.path.startsWith('/compliance') }">
            <span class="nav-icon">📋</span>
            <span>コンプライアンス</span>
          </router-link>
        </li>
        <li>
          <router-link to="/audits" :class="{ active: $route.path.startsWith('/audits') }">
            <span class="nav-icon">🔍</span>
            <span>監査管理</span>
          </router-link>
        </li>
      </ul>
      <div class="sidebar-footer">
        <span :class="['health-dot', healthStatus]" :title="healthStatus"></span>
        <span class="health-label">API {{ healthStatus === 'ok' ? 'オンライン' : 'オフライン' }}</span>
      </div>
    </nav>

    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { healthApi } from '@/api/health'

const healthStatus = ref<'ok' | 'error' | 'unknown'>('unknown')

onMounted(async () => {
  try {
    const result = await healthApi.check()
    healthStatus.value = result.status === 'ok' ? 'ok' : 'error'
  } catch {
    healthStatus.value = 'error'
  }
})
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #333; background: #f8f9fa; }
button { cursor: pointer; padding: 0.5rem 1rem; background: #1565c0; color: #fff; border: none; border-radius: 4px; font-size: 0.9rem; }
button:hover { background: #0d47a1; }
select { padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; background: #fff; font-size: 0.9rem; }
</style>

<style scoped>
#app { display: flex; min-height: 100vh; }
.sidebar { width: 220px; background: #1a237e; color: #fff; display: flex; flex-direction: column; flex-shrink: 0; }
.logo { display: flex; align-items: center; gap: 0.5rem; padding: 1.25rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 1.2rem; font-weight: 700; }
.logo-icon { font-size: 1.5rem; }
.nav-links { list-style: none; padding: 0.75rem 0; flex: 1; }
.nav-links li a { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; color: rgba(255,255,255,0.75); text-decoration: none; font-size: 0.9rem; transition: background 0.2s; }
.nav-links li a:hover, .nav-links li a.active { background: rgba(255,255,255,0.12); color: #fff; }
.nav-links li a.active { border-left: 3px solid #90caf9; }
.nav-icon { font-size: 1rem; width: 1.25rem; text-align: center; }
.sidebar-footer { padding: 1rem; border-top: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: rgba(255,255,255,0.6); }
.health-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.health-dot.ok { background: #69f0ae; }
.health-dot.error { background: #ff5252; }
.health-dot.unknown { background: #bdbdbd; }
.main-content { flex: 1; overflow-y: auto; }
</style>
