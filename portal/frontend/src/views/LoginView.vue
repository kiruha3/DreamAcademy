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

const email = ref('')
const password = ref('')

function handleLogin() {
  alert('Авторизация будет реализована после интеграции с Moodle SSO')
}
</script>
