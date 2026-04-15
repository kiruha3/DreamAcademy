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

const firstname = ref('')
const lastname = ref('')
const email = ref('')
const password = ref('')

function handleRegister() {
  alert('Регистрация будет реализована после интеграции с Moodle SSO')
}
</script>
