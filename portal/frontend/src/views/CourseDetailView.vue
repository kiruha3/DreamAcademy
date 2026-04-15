<template>
  <section class="course-detail">
    <div class="container">
      <div class="back">
        <router-link to="/courses">← Назад к курсам</router-link>
      </div>
      <h2>{{ courseName }}</h2>
      <p v-if="loading" class="loading">Загрузка содержимого...</p>
      <div v-else>
        <div v-for="section in sections" :key="section.id" class="section-card">
          <h3 class="section-title">{{ section.name || 'Раздел ' + section.section }}</h3>
          <div class="modules">
            <div v-for="mod in section.modules" :key="mod.id" class="module-item" :class="'mod-' + mod.modname">
              <img v-if="mod.modicon" :src="mod.modicon" alt="" class="mod-icon" />
              <div class="mod-body">
                <div v-if="mod.modname === 'label'" class="mod-label" v-html="mod.description || mod.name"></div>
                <template v-else>
                  <div class="mod-name">{{ mod.name }}</div>
                  <div class="mod-meta">{{ mod.modplural || typeLabel(mod.modname) }}</div>
                  <a v-if="mod.url" :href="mod.url" target="_blank" class="mod-link">Открыть материал →</a>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchCourseContents, fetchCourses } from '@/api/client.js'

const route = useRoute()
const sections = ref([])
const courseName = ref('Курс')
const loading = ref(true)

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

onMounted(async () => {
  try {
    const [contentsData, coursesData] = await Promise.all([
      fetchCourseContents(route.params.id),
      fetchCourses().catch(() => ({ courses: [] })),
    ])
    sections.value = contentsData.contents || contentsData.sections || []
    const cid = Number(route.params.id)
    const match = (coursesData.courses || []).find(c => c.id === cid)
    if (match) {
      courseName.value = match.fullname || match.shortname || 'Курс'
    }
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
.course-detail h2 { font-size: 32px; color: var(--color-dark); margin-bottom: 24px; }
.section-card { background: #fff; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.section-title { font-size: 20px; margin-bottom: 14px; color: #111827; }
.modules { display: flex; flex-direction: column; gap: 12px; }
.module-item { display: flex; align-items: flex-start; gap: 12px; padding: 14px; border: 1px solid #f3f4f6; border-radius: 10px; background: #fafafa; }
.mod-icon { width: 28px; height: 28px; flex-shrink: 0; }
.mod-body { flex: 1; }
.mod-name { font-weight: 600; color: #111827; }
.mod-meta { font-size: 13px; color: #6b7280; margin-top: 2px; }
.mod-link { display: inline-block; margin-top: 8px; color: var(--color-primary); font-size: 14px; text-decoration: none; }
.mod-link:hover { text-decoration: underline; }
.mod-label :deep(p) { margin: 0; }
.mod-label :deep(.alert) { padding: 10px 14px; border-radius: 8px; background: #e0f2fe; color: #0c4a6e; }
.loading { color: #6b7280; }
</style>
