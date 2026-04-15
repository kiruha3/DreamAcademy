<template>
  <section class="course-detail">
    <div class="container">
      <div class="back">
        <router-link to="/courses">← Назад к курсам</router-link>
      </div>
      <div class="course-hero">
        <img
          v-if="courseImage"
          :src="courseImage"
          :alt="courseName"
          class="course-hero-image"
        />
        <div v-else class="course-hero-placeholder">
          <span class="course-hero-initial">{{ courseInitial }}</span>
        </div>
      </div>

      <h2>{{ courseName }}</h2>

      <div v-if="progress.total > 0" class="progress-bar-wrap">
        <div class="progress-label">Прогресс: {{ progress.completed }} из {{ progress.total }} модулей</div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
      </div>

      <p v-if="loading" class="loading">Загрузка содержимого...</p>
      <div v-else>
        <div v-for="section in sections" :key="section.id" class="section-card">
          <h3 class="section-title">{{ section.name || 'Раздел ' + section.section }}</h3>
          <div class="modules">
            <div v-for="mod in section.modules" :key="mod.id" class="module-item" :class="['mod-' + mod.modname, { completed: isCompleted(mod.id) }]">
              <img v-if="mod.modicon" :src="mod.modicon" alt="" class="mod-icon" />
              <div class="mod-body">
                <div class="mod-header">
                  <div class="mod-name">{{ mod.name }}</div>
                  <div class="mod-type">{{ mod.modplural || typeLabel(mod.modname) }}</div>
                  <span v-if="isCompleted(mod.id)" class="badge-completed">✓ Выполнено</span>
                </div>

                <div class="mod-renderer">
                  <ModuleRenderer :data="mod" />
                </div>

                <div class="mod-actions">
                  <button v-if="canComplete(mod.modname) && !isCompleted(mod.id)" class="btn-complete" @click="handleComplete(mod.id)">
                    Отметить пройденным
                  </button>
                  <span v-else-if="isCompleted(mod.id)" class="completed-hint">Модуль выполнен</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { fetchCourseContents, fetchCourses, fetchCourseProgress, markModuleComplete } from '@/api/client.js'
import ModuleRenderer from '@/components/modules/ModuleRenderer.vue'

const route = useRoute()
const sections = ref([])
const courseName = ref('Курс')
const courseImage = ref('')
const loading = ref(true)
const progress = ref({ completed: 0, total: 0, modules: [] })

const progressPercent = computed(() => {
  if (!progress.value.total) return 0
  return Math.round((progress.value.completed / progress.value.total) * 100)
})

const courseInitial = computed(() => {
  return courseName.value.trim().charAt(0).toUpperCase()
})

function typeLabel(modname) {
  const map = {
    page: 'Страница',
    url: 'Ссылка',
    quiz: 'Тест',
    assign: 'Задание',
    forum: 'Форум',
    label: 'Ярлык',
    resource: 'Файл',
  }
  return map[modname] || modname
}

function isCompleted(cmid) {
  const m = progress.value.modules.find(m => m.cmid === cmid)
  return m ? m.completed : false
}

function canComplete(modname) {
  // Page, URL, Label can be marked complete inline
  // Quiz, Assign, Forum will have their own completion logic in later phases
  return ['page', 'url', 'label'].includes(modname)
}

async function handleComplete(cmid) {
  try {
    await markModuleComplete(route.params.id, cmid)
    await loadProgress()
  } catch (e) {
    alert('Не удалось отметить модуль: ' + e.message)
  }
}

async function loadProgress() {
  try {
    const data = await fetchCourseProgress(route.params.id)
    progress.value = {
      completed: data.completed_count || 0,
      total: data.total_count || 0,
      modules: data.modules || [],
    }
  } catch (e) {
    console.error('Failed to load progress', e)
  }
}

onMounted(async () => {
  try {
    const [contentsData, coursesData] = await Promise.all([
      fetchCourseContents(route.params.id),
      fetchCourses().catch(() => ({ courses: [] })),
    ])
    const cid = Number(route.params.id)
    sections.value = (contentsData.contents || contentsData.sections || []).map(section => ({
      ...section,
      modules: (section.modules || []).map(mod => ({
        ...mod,
        course_id: cid,
        cmid: mod.id
      }))
    }))
    const match = (coursesData.courses || []).find(c => c.id === cid)
    if (match) {
      courseName.value = match.fullname || match.shortname || 'Курс'
      courseImage.value = match.imageUrl || ''
    }
    await loadProgress()
  } catch (e) {
    console.error('Failed to load course contents', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.course-detail { padding: 40px 0; background: var(--color-bg-light); min-height: 60vh; }
.back { margin-bottom: 16px; }
.back a { color: var(--color-primary); text-decoration: none; font-weight: 500; }
.back a:hover { text-decoration: underline; }
.course-detail h2 { font-size: 32px; color: var(--color-dark); margin-bottom: 16px; }
.course-hero { margin-bottom: 20px; border-radius: 12px; overflow: hidden; background: #f3f4f6; }
.course-hero-image { width: 100%; height: 260px; object-fit: contain; display: block; }
.course-hero-placeholder { width: 100%; height: 260px; background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-primary) 100%); display: flex; align-items: center; justify-content: center; }
.course-hero-initial { font-size: 120px; font-weight: 700; color: rgba(255,255,255,0.9); line-height: 1; }

.progress-bar-wrap { margin-bottom: 24px; }
.progress-label { font-size: 14px; color: #374151; margin-bottom: 6px; }
.progress-bar { height: 10px; background: #e5e7eb; border-radius: 999px; overflow: hidden; max-width: 400px; }
.progress-fill { height: 100%; background: var(--color-primary); transition: width 0.3s ease; }

.section-card { background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.section-title { font-size: 20px; margin-bottom: 14px; color: #111827; }
.modules { display: flex; flex-direction: column; gap: 12px; }
.module-item { display: flex; align-items: flex-start; gap: 12px; padding: 14px; border: 1px solid #f3f4f6; border-radius: 10px; background: #fafafa; }
.module-item.completed { background: #f0fdf4; border-color: #bbf7d0; }
.mod-icon { width: 28px; height: 28px; flex-shrink: 0; }
.mod-body { flex: 1; }
.mod-header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
.mod-name { font-weight: 600; color: #111827; }
.mod-type { font-size: 13px; color: #6b7280; }
.badge-completed { font-size: 12px; color: #15803d; background: #dcfce7; padding: 2px 8px; border-radius: 999px; }
.mod-renderer { margin: 8px 0; }
.mod-actions { margin-top: 10px; }
.btn-complete { background: var(--color-primary); color: #fff; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.btn-complete:hover { opacity: 0.92; }
.completed-hint { font-size: 13px; color: #6b7280; }
.loading { color: #6b7280; }
</style>
