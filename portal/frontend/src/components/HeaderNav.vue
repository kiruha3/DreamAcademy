<template>
  <header class="header">
    <div class="container header-inner">
      <router-link to="/" class="logo-link">
        <img
          src="https://static.tildacdn.com/tild6333-3362-4538-b337-643737376534/DreamDocs_logo_1.png"
          alt="DreamDocs"
          class="logo"
        />
        <span class="logo-text">academy</span>
      </router-link>
      <nav class="nav">
        <router-link to="/courses">Курсы</router-link>
        <router-link v-if="authStore.isAuthenticated" to="/dashboard">Личный кабинет</router-link>
        <router-link v-if="authStore.user?.role === 'admin'" to="/admin">Админ-панель</router-link>
        <span v-if="authStore.isAuthenticated && authStore.user" class="user-name">
          {{ authStore.user.firstname }}
        </span>
        <router-link v-if="!authStore.isAuthenticated" to="/login" class="btn-primary">Войти</router-link>
        <button v-else class="btn-primary" @click="logout">Выйти</button>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

function logout() {
  authStore.logout()
  router.push('/')
}
</script>

<style scoped>
.header { background: var(--color-bg); border-bottom: 1px solid var(--color-bg-light); padding: 16px 0; }
.header-inner { display: flex; justify-content: space-between; align-items: center; }
.logo-link { display: inline-flex; align-items: flex-end; gap: 6px; text-decoration: none; }
.logo { height: 32px; }
.logo-text {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-dark);
  letter-spacing: 0.04em;
  text-transform: lowercase;
  line-height: 1;
  transform: translateY(-10%);
}
.nav a, .nav button, .nav span { margin-left: 24px; text-decoration: none; color: var(--color-dark); font-weight: 500; }
.nav a:hover { color: var(--color-primary); }
.nav .btn-primary { margin-left: 24px; padding: 8px 16px; font-size: 14px; border: none; cursor: pointer; }
.nav .user-name { color: var(--color-primary); }
</style>
