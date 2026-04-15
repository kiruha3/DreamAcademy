<template>
  <div class="url-viewer">
    <div v-if="detail.intro" class="url-intro" v-html="sanitized(detail.intro)"></div>
    <a :href="detail.externalurl" target="_blank" rel="noopener" class="url-link">
      Перейти по ссылке →
    </a>
    <span class="url-meta">{{ detail.externalurl }}</span>
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
    console.error('Failed to load url detail', e)
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
.url-viewer { display: flex; flex-direction: column; gap: 6px; }
.url-link { display: inline-flex; align-items: center; gap: 6px; color: #fff; background: var(--color-primary); padding: 8px 14px; border-radius: 8px; text-decoration: none; width: fit-content; }
.url-link:hover { opacity: 0.92; }
.url-meta { font-size: 12px; color: #6b7280; }
.url-intro { margin: 0 0 4px; color: #374151; }
</style>
