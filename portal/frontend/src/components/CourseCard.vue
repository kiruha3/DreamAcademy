<template>
  <div class="course-card">
    <h3>{{ course.fullname || course.shortname || 'Курс' }}</h3>
    <p>{{ stripHtml(course.summary) || 'Описание появится позже' }}</p>
    <div class="actions">
      <router-link :to="`/courses/${course.id}`" class="btn-primary">Подробнее</router-link>
      <button v-if="canInvite" class="btn-secondary" @click="$emit('invite', course.id)">Пригласить</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({ course: { type: Object, required: true } })
defineEmits(['invite'])

const authStore = useAuthStore()
const canInvite = computed(() => {
  return ['admin', 'teacher', 'course_creator'].includes(authStore.user?.role)
})

function stripHtml(html) {
  if (!html) return ''
  return html.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').trim()
}
</script>

<style scoped>
.course-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
}
.course-card h3 { color: var(--color-dark); margin-bottom: 8px; }
.course-card p { margin-bottom: 16px; flex: 1; }
.actions { display: flex; gap: 10px; }
.actions .btn-secondary { background: #e5e7eb; color: #374151; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 14px; }
</style>
