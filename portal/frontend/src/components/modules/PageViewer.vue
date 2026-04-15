<template>
  <div class="page-viewer">
    <div v-if="data.intro" class="page-intro" v-html="sanitized(data.intro)"></div>
    <div v-if="data.content" class="page-content" v-html="sanitized(data.content)"></div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: { type: Object, required: true }
})

function sanitized(html) {
  if (!html) return ''
  // Simple whitelist sanitizer
  const allowed = /<(\/?)(b|i|em|strong|u|p|br|hr|h[1-6]|ul|ol|li|div|span|a|img|table|thead|tbody|tr|td|th|blockquote|pre|code|sup|sub)(\s+[^>]*)?>/gi
  return html.replace(/<[^>]+>/g, (tag) => {
    return allowed.test(tag) ? tag : ''
  })
}
</script>

<style scoped>
.page-viewer { line-height: 1.6; color: #111827; }
.page-intro { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb; }
.page-content :deep(img) { max-width: 100%; height: auto; }
.page-content :deep(a) { color: var(--color-primary); }
.page-content :deep(table) { width: 100%; border-collapse: collapse; margin: 12px 0; }
.page-content :deep(th), .page-content :deep(td) { border: 1px solid #e5e7eb; padding: 8px; }
</style>
