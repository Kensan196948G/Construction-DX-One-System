<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <span class="login-icon">🔐</span>
        <h2>ZeroTrust ID Governance</h2>
        <p class="login-subtitle">サインイン</p>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">ユーザー名</label>
          <input
            id="username"
            v-model.trim="username"
            type="text"
            placeholder="username"
            autocomplete="username"
            :disabled="loading"
          />
        </div>

        <div class="form-group">
          <label for="password">パスワード</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="••••••••"
            autocomplete="current-password"
            :disabled="loading"
          />
        </div>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <button type="submit" class="login-btn" :disabled="loading || !username || !password">
          <span v-if="loading" class="spinner" />
          <span v-else>ログイン</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push({ name: 'dashboard' })
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : 'ログインに失敗しました'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #181825;
}

.login-card {
  background: #1e1e2e;
  border: 1px solid #313244;
  border-radius: 12px;
  padding: 2.5rem 2rem;
  width: 100%;
  max-width: 380px;
}

.login-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.login-icon {
  font-size: 2rem;
}

.login-header h2 {
  font-size: 1.25rem;
  margin-top: 0.5rem;
  color: #cdd6f4;
}

.login-subtitle {
  font-size: 0.85rem;
  color: #a6adc8;
  margin-top: 0.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-bottom: 1rem;
}

.form-group label {
  font-size: 0.85rem;
  color: #a6adc8;
}

.form-group input {
  padding: 0.6rem 0.75rem;
  font-size: 0.95rem;
}

.error-msg {
  color: #f38ba8;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

.login-btn {
  width: 100%;
  padding: 0.65rem;
  font-size: 0.95rem;
  font-weight: 600;
  background: #89b4fa;
  color: #1e1e2e;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.login-btn:hover:not(:disabled) {
  background: #74c7ec;
}

.login-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid #1e1e2e;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
