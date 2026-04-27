<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-header">
        <span class="icon">🛡️</span>
        <h2>CSIEM にログイン</h2>
      </div>
      <form @submit.prevent="handleLogin">
        <div class="field">
          <label>ユーザー名</label>
          <input v-model="username" type="text" placeholder="username" required autocomplete="username" />
        </div>
        <div class="field">
          <label>パスワード</label>
          <input v-model="password" type="password" placeholder="password" required autocomplete="current-password" />
        </div>
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button type="submit" :disabled="busy" class="login-btn">
          {{ busy ? 'ログイン中...' : 'ログイン' }}
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
const busy = ref(false)

async function handleLogin() {
  error.value = ''
  busy.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'ログインに失敗しました'
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; background: #181825;
}
.login-card {
  background: #1e1e2e; border: 1px solid #313244; border-radius: 10px;
  padding: 2rem; width: 360px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.login-header {
  display: flex; align-items: center; gap: 0.5rem;
  margin-bottom: 1.5rem; font-size: 1.2rem;
}
.login-header .icon { font-size: 1.6rem; }
.field { margin-bottom: 1rem; }
.field label { display: block; margin-bottom: 0.3rem; font-size: 0.85rem; color: #a6adc8; }
.field input {
  display: block; width: 100%;
  background: #313244; border: 1px solid #45475a; color: #cdd6f4;
  padding: 0.5rem 0.6rem; border-radius: 4px;
}
.login-btn {
  width: 100%; margin-top: 0.5rem; padding: 0.6rem;
  background: #89b4fa; color: #1e1e2e; border: none; border-radius: 4px;
  font-weight: 600; cursor: pointer;
}
.login-btn:hover { background: #74c7ec; }
.login-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.error-msg { color: #f38ba8; font-size: 0.85rem; margin: 0.5rem 0; }
</style>
