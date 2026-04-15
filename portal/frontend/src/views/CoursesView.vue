<template>
  <section class="courses">
    <div class="container">
      <h2>Каталог курсов</h2>
      <p v-if="loading" class="loading">Загрузка курсов...</p>
      <p v-else-if="error" class="loading">Ошибка загрузки: {{ error }}</p>
      <div v-else class="courses-grid">
        <CourseCard v-for="course in visibleCourses" :key="course.id" :course="course" />
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchCourses } from '../api/client.js'
import CourseCard from '../components/CourseCard.vue'

const courses = ref([])
const loading = ref(true)
const error = ref(null)

const visibleCourses = computed(() =>
  courses.value.filter(c => c.id !== 1)
)

onMounted(async () => {
  try {
    const data = await fetchCourses()
    courses.value = data.courses || []
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.courses { padding: 60px 0; background: var(--color-bg-light); min-height: 60vh; }
.courses h2 { text-align: center; font-size: 36px; color: var(--color-dark); margin-bottom: 48px; }
.courses-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 24px; }
</style>
