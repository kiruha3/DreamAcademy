<template>
  <div class="auth-page">
    <div class="auth-box">
      <h2>Вход в Академию</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Email</label>
          <input v-model="email" type="email" required />
        </div>
        <div class="form-group">
          <label>Пароль</label>
          <input v-model="password" type="password" required />
        </div>
        <div v-if="error" class="error">{{ error }}</div>
        <button type="submit" class="btn-primary btn-full">Войти</button>
      </form>
      <div class="auth-links">
        <p>Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const email = ref('')
const password = ref('')
const error = ref('')
const router = useRouter()
const authStore = useAuthStore()

async function handleLogin() {
  error.value = ''
  console.log('Login attempt:', email.value, password.value)
  try {
    await authStore.signIn(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    console.error('Login error:', e)
    error.value = 'Неверный email или пароль'
  }
}
</script>
