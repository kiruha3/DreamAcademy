<template>
  <div class="url-viewer">
    <p v-if="data.intro" class="url-intro">{{ data.intro }}</p>
    <a :href="data.externalurl" target="_blank" rel="noopener" class="url-link">
      Перейти по ссылке →
    </a>
    <span class="url-meta">{{ data.externalurl }}</span>
  </div>
</template>

<script setup>
const props = defineProps({
  data: { type: Object, required: true }
})
</script>

<style scoped>
.url-viewer { display: flex; flex-direction: column; gap: 6px; }
.url-link { display: inline-flex; align-items: center; gap: 6px; color: #fff; background: var(--color-primary); padding: 8px 14px; border-radius: 8px; text-decoration: none; width: fit-content; }
.url-link:hover { opacity: 0.92; }
.url-meta { font-size: 12px; color: #6b7280; }
.url-intro { margin: 0 0 4px; color: #374151; }
</style>
