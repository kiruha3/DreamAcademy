<template>
  <div class="generic-viewer">
    <div v-if="detail.intro" class="generic-intro" v-html="sanitized(detail.intro)"></div>
    <div class="generic-meta">
      <span v-if="metaItems.length">{{ metaItems.join(' • ') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
    console.error('Failed to load module detail', e)
  }
})

const metaItems = computed(() => {
  const items = []
  if (detail.value.modname === 'quiz') {
    if (detail.value.sumgrades) items.push(`Макс. балл: ${detail.value.sumgrades}`)
    if (detail.value.grade) items.push(`Оценка: ${detail.value.grade}`)
  }
  if (detail.value.modname === 'assign') {
    if (detail.value.duedate) items.push(`Дедлайн: ${formatDate(detail.value.duedate)}`)
    if (detail.value.grade) items.push(`Макс. оценка: ${detail.value.grade}`)
  }
  if (detail.value.modname === 'forum') {
    items.push(`Тип: ${detail.value.type === 'news' ? 'Новости' : 'Общий'}`)
  }
  return items
})

function formatDate(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  return d.toLocaleDateString('ru-RU')
}

function sanitized(html) {
  if (!html) return ''
  const allowed = /<(\/?)(b|i|em|strong|u|p|br|hr|h[1-6]|ul|ol|li|div|span|a|img|table|thead|tbody|tr|td|th|blockquote|pre|code|sup|sub)(\s+[^>]*)?>/gi
  return html.replace(/<[^>]+>/g, (tag) => {
    return allowed.test(tag) ? tag : ''
  })
}
</script>

<style scoped>
.generic-viewer { }
.generic-intro { margin: 0 0 8px; color: #374151; white-space: pre-line; }
.generic-meta { font-size: 13px; color: #6b7280; }
</style>
