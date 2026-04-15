<template>
  <div class="course-card">
    <h3>{{ course.fullname || course.shortname || 'Курс' }}</h3>
    <p>{{ stripHtml(course.summary) || 'Описание появится позже' }}</p>
    <router-link :to="`/courses/${course.id}`" class="btn-primary">Подробнее</router-link>
  </div>
</template>

<script setup>
defineProps({ course: { type: Object, required: true } })

function stripHtml(html) {
  if (!html) return ''
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  return tmp.textContent || tmp.innerText || ''
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
</style>
