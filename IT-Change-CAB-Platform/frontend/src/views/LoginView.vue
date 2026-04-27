<template>
  <div class="login-view">
    <div class="login-card">
      <div class="login-header">
        <span class="login-icon">🔄</span>
        <h2>CAB Platform</h2>
        <p class="login-subtitle">Change Approval Board</p>
      </div>
      <form @submit.prevent="handleLogin">
        <div class="form-row">
          <label>ユーザー名</label>
          <input
            v-model="username"
            type="text"
            placeholder="ユーザー名を入力"
            required
            autocomplete="username"
          />
        </div>
        <div class="form-row">
          <label>パスワード</label>
          <input
            v-model="password"
            type="password"
            placeholder="パスワードを入力"
            required
            autocomplete="current-password"
          />
        </div>
        <p v-if="errorMsg" class="error">{{ errorMsg }}</p>
        <button type="submit" class="login-btn" :disabled="authStore.loading">
          {{ authStore.loading ? 'ログイン中...' : 'ログイン' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const errorMsg = ref<string | null>(null)

async function handleLogin() {
  errorMsg.value = null
  const ok = await authStore.login(username.value, password.value)
  if (ok) {
    router.push('/')
  } else {
    errorMsg.value = authStore.error ?? 'ログインに失敗しました'
  }
}
</script>

<style scoped>
.login-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #181825;
}
.login-card {
  background: #1e1e2e;
  border: 1px solid #45475a;
  border-radius: 12px;
  padding: 2.5rem 2rem;
  width: 100%;
  max-width: 400px;
}
.login-header {
  text-align: center;
  margin-bottom: 2rem;
}
.login-icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 0.5rem;
}
.login-header h2 {
  font-size: 1.5rem;
  color: #cdd6f4;
  margin-bottom: 0.25rem;
}
.login-subtitle {
  font-size: 0.85rem;
  color: #6c7086;
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 1rem;
}
.form-row label {
  font-size: 0.85rem;
  color: #a6adc8;
}
.form-row input {
  padding: 0.6rem 0.75rem;
  font-size: 0.95rem;
}
.login-btn {
  width: 100%;
  padding: 0.65rem;
  font-size: 1rem;
  margin-top: 0.5rem;
  background: #89b4fa;
  color: #1e1e2e;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}
.login-btn:hover {
  background: #74c7ec;
}
.login-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.error {
  color: #f38ba8;
  font-size: 0.85rem;
  text-align: center;
  margin-bottom: 0.5rem;
}
</style>
