<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <span class="icon">🛡️</span>
        <h2>BCP/ITSCM システム</h2>
        <p>ログイン</p>
      </div>
      <form @submit.prevent="handleLogin" class="login-form">
        <label>
          ユーザー名
          <input v-model="username" type="text" autocomplete="username" required />
        </label>
        <label>
          パスワード
          <input v-model="password" type="password" autocomplete="current-password" required />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">
          {{ loading ? 'ログイン中...' : 'ログイン' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref<string | null>(null)
const loading = ref(false)

async function handleLogin() {
  if (!username.value.trim() || !password.value.trim()) {
    error.value = 'ユーザー名とパスワードを入力してください'
    return
  }
  loading.value = true
  error.value = null
  const ok = await auth.login({ username: username.value, password: password.value })
  loading.value = false
  if (ok) {
    router.push('/')
  } else {
    error.value = 'ログインに失敗しました'
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}
.login-card {
  background: #1e1e2e;
  border: 1px solid #45475a;
  border-radius: 8px;
  padding: 2rem;
  width: 360px;
}
.login-header {
  text-align: center;
  margin-bottom: 1.5rem;
}
.login-header .icon { font-size: 2rem; }
.login-header h2 { margin: 0.5rem 0 0.25rem; }
.login-header p { color: #a6adc8; font-size: 0.9rem; }
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.login-form label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: #a6adc8;
}
.login-form button {
  margin-top: 0.5rem;
  padding: 0.6rem;
}
.error { color: #f38ba8; font-size: 0.85rem; text-align: center; }
</style>
