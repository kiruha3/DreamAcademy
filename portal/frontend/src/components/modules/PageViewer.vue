<template>
  <div class="page-viewer">
    <div v-if="detail.intro" class="page-intro" v-html="sanitized(detail.intro)"></div>
    <div v-if="detail.content" class="page-content" v-html="sanitized(detail.content)"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchModuleDetail } from '@/api/client.js'

const props = defineProps({
  data: { type: Object, required: true }
})

const detail = ref({ ...props.data })

onMounted(async () => {
  try {
    const res = await fetchModuleDetail(props.data.course_id, props.data.cmid)
    detail.value = { ...detail.value, ...res }
  } catch (e) {
    console.error('Failed to load page detail', e)
  }
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
.page-viewer { line-height: 1.6; color: #111827; }
.page-intro { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb; }
.page-content :deep(img) { max-width: 100%; height: auto; }
.page-content :deep(a) { color: var(--color-primary); }
.page-content :deep(table) { width: 100%; border-collapse: collapse; margin: 12px 0; }
.page-content :deep(th), .page-content :deep(td) { border: 1px solid #e5e7eb; padding: 8px; }
</style>
