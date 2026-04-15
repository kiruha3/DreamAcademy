<template>
  <div class="auth-page">
    <div class="auth-box">
      <h2>Регистрация</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>Имя</label>
          <input v-model="firstname" type="text" required />
        </div>
        <div class="form-group">
          <label>Фамилия</label>
          <input v-model="lastname" type="text" required />
        </div>
        <div class="form-group">
          <label>Email</label>
          <input v-model="email" type="email" required />
        </div>
        <div class="form-group">
          <label>Пароль</label>
          <input v-model="password" type="password" required />
        </div>
        <div v-if="error" class="error">{{ error }}</div>
        <button type="submit" class="btn-primary btn-full">Зарегистрироваться</button>
      </form>
      <div class="auth-links">
        <p>Уже есть аккаунт? <router-link to="/login">Войти</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const firstname = ref('')
const lastname = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const router = useRouter()
const authStore = useAuthStore()

async function handleRegister() {
  error.value = ''
  const payload = {
    email: email.value,
    username: email.value.split('@')[0] + '_' + Math.floor(Math.random() * 1000),
    firstname: firstname.value,
    lastname: lastname.value,
    password: password.value,
    role: 'student',
  }
  console.log('Register attempt:', payload.email)
  try {
    await authStore.signUp(payload)
    router.push('/dashboard')
  } catch (e) {
    console.error('Register error:', e)
    error.value = 'Ошибка регистрации. Возможно, email уже занят.'
  }
}
</script>
