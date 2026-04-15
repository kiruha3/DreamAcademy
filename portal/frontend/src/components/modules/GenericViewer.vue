<template>
  <div class="generic-viewer">
    <p v-if="data.intro" class="generic-intro">{{ data.intro }}</p>
    <div class="generic-meta">
      <span v-if="metaItems.length">{{ metaItems.join(' • ') }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Object, required: true }
})

const metaItems = computed(() => {
  const items = []
  if (props.data.modname === 'quiz') {
    if (props.data.sumgrades) items.push(`Макс. балл: ${props.data.sumgrades}`)
    if (props.data.grade) items.push(`Оценка: ${props.data.grade}`)
  }
  if (props.data.modname === 'assign') {
    if (props.data.duedate) items.push(`Дедлайн: ${formatDate(props.data.duedate)}`)
    if (props.data.grade) items.push(`Макс. оценка: ${props.data.grade}`)
  }
  if (props.data.modname === 'forum') {
    items.push(`Тип: ${props.data.type === 'news' ? 'Новости' : 'Общий'}`)
  }
  return items
})

function formatDate(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  return d.toLocaleDateString('ru-RU')
}
</script>

<style scoped>
.generic-viewer { }
.generic-intro { margin: 0 0 8px; color: #374151; white-space: pre-line; }
.generic-meta { font-size: 13px; color: #6b7280; }
</style>
