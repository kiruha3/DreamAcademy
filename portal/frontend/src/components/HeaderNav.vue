<template>
  <header class="header">
    <div class="container header-inner">
      <router-link to="/" class="logo-link">
        <img
          src="https://static.tildacdn.com/tild6333-3362-4538-b337-643737376534/DreamDocs_logo_1.png"
          alt="DreamDocs"
          class="logo"
        />
      </router-link>
      <nav class="nav">
        <router-link to="/courses">Курсы</router-link>
        <router-link to="/dashboard">Личный кабинет</router-link>
        <router-link to="/login" class="btn-primary">Войти</router-link>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.header { background: var(--color-bg); border-bottom: 1px solid var(--color-bg-light); padding: 16px 0; }
.header-inner { display: flex; justify-content: space-between; align-items: center; }
.logo { height: 32px; }
.nav a { margin-left: 24px; text-decoration: none; color: var(--color-dark); font-weight: 500; }
.nav a:hover { color: var(--color-primary); }
.nav .btn-primary { margin-left: 24px; padding: 8px 16px; font-size: 14px; }
</style>
