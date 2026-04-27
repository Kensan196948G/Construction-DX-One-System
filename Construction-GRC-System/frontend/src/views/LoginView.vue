<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>GRC System</h1>
        <p>ログイン</p>
      </div>
      <form @submit.prevent="handleLogin">
        <div class="field">
          <label for="username">ユーザー名</label>
          <input id="username" v-model="username" type="text" required autocomplete="username" />
        </div>
        <div class="field">
          <label for="password">パスワード</label>
          <input id="password" v-model="password" type="password" required autocomplete="current-password" />
        </div>
        <p v-if="error" class="error-msg">{{ error }}</p>
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

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'ログインに失敗しました'
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
  background: #f0f2f5;
}
.login-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  width: 360px;
}
.login-header {
  text-align: center;
  margin-bottom: 1.5rem;
}
.login-header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #1a237e;
}
.login-header p {
  margin: 0.25rem 0 0;
  color: #666;
}
.field {
  margin-bottom: 1rem;
}
.field label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.85rem;
  color: #555;
}
.field input {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.9rem;
}
.field input:focus {
  outline: none;
  border-color: #1565c0;
  box-shadow: 0 0 0 2px rgba(21, 101, 192, 0.15);
}
button {
  width: 100%;
  padding: 0.65rem;
  background: #1565c0;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 0.95rem;
}
button:hover:not(:disabled) {
  background: #0d47a1;
}
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.error-msg {
  color: #e53935;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}
</style>
