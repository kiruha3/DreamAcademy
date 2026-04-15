<template>
  <div class="label-viewer" v-html="sanitized(data.intro || data.content)"></div>
</template>

<script setup>
const props = defineProps({
  data: { type: Object, required: true }
})

function sanitized(html) {
  if (!html) return ''
  const allowed = /<(\/?)(b|i|em|strong|u|p|br|hr|h[1-6]|ul|ol|li|div|span|a|img|table|thead|tbody|tr|td|th|blockquote|pre|code|sup|sub)(\s+[^>]*)?>/gi
  return html.replace(/<[^>]+>/g, (tag) => {
    return allowed.test(tag) ? tag : ''
  })
}
</script>

<style scoped>
.label-viewer :deep(p) { margin: 0; }
.label-viewer :deep(.alert) { padding: 10px 14px; border-radius: 8px; background: #e0f2fe; color: #0c4a6e; }
.label-viewer :deep(img) { max-width: 100%; height: auto; }
</style>
