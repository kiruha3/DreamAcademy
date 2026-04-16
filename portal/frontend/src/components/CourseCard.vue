<template>
  <div class="course-card">
    <div class="course-media">
      <img
        v-if="course.imageUrl"
        :src="course.imageUrl"
        :alt="course.fullname || 'Курс'"
        class="course-image"
      />
      <div v-else class="course-image-placeholder">
        <span class="course-initial">{{ initial }}</span>
      </div>
    </div>
    <div class="course-body">
      <h3>{{ course.fullname || course.shortname || 'Курс' }}</h3>
      <p>{{ stripHtml(course.summary) || 'Описание появится позже' }}</p>
      <div class="actions">
        <router-link :to="`/courses/${course.id}`" class="btn-primary">Подробнее</router-link>
        <button v-if="canInvite" class="btn-secondary" @click="$emit('invite', course.id)">Пригласить</button>
      </div>
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

const initial = computed(() => {
  const name = props.course.fullname || props.course.shortname || 'К'
  return name.trim().charAt(0).toUpperCase()
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
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.course-media { width: 100%; height: 160px; display: flex; align-items: center; justify-content: center; background: #f3f4f6; }
.course-image {
  max-width: 100%;
  max-height: 160px;
  width: auto;
  height: auto;
  display: block;
}
.course-image-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-primary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.course-initial {
  font-size: 64px;
  font-weight: 700;
  color: rgba(255,255,255,0.9);
  line-height: 1;
}
.course-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  flex: 1;
}
.course-body h3 { color: var(--color-dark); margin-bottom: 8px; }
.course-body p { margin-bottom: 16px; flex: 1; }
.actions { display: flex; gap: 10px; }
.actions .btn-secondary { background: #e5e7eb; color: #374151; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; text-decoration: none; font-size: 14px; }
</style>
