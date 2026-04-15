<template>
  <HeaderNav />
  <main>
    <router-view />
  </main>
  <footer class="footer">
    <div class="container">
      <p>&copy; 2026 DreamDocs. Все права защищены.</p>
    </div>
  </footer>
</template>

<script setup>
import HeaderNav from './components/HeaderNav.vue'
</script>
