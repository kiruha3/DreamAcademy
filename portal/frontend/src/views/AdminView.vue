<template>
  <section class="admin">
    <div class="container">
      <h2>Админ-панель</h2>
      <div class="tabs">
        <button :class="{ active: tab === 'users' }" @click="tab = 'users'">Пользователи</button>
        <button :class="{ active: tab === 'courses' }" @click="tab = 'courses'">Курсы</button>
      </div>

      <div v-if="tab === 'users'" class="tab-content">
        <p v-if="loading">Загрузка...</p>
        <table v-else class="data-table">
          <thead>
            <tr><th>ID</th><th>Email</th><th>Имя</th><th>Роль</th><th>Moodle ID</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td>{{ u.email }}</td>
              <td>{{ u.firstname }} {{ u.lastname }}</td>
              <td>{{ u.role }}</td>
              <td>{{ u.moodle_user_id }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="tab-content">
        <form class="create-form" @submit.prevent="handleCreateCourse">
          <input v-model="newCourse.fullname" type="text" placeholder="Название курса" required />
          <input v-model="newCourse.shortname" type="text" placeholder="Краткое название (код)" required />
          <textarea v-model="newCourse.summary" placeholder="Описание" rows="2"></textarea>
          <button type="submit" class="btn-primary">Создать курс</button>
        </form>
        <div v-if="courseMessage" class="message">{{ courseMessage }}</div>

        <p v-if="coursesLoading" class="loading">Загрузка курсов...</p>
        <table v-else class="data-table">
          <thead>
            <tr><th>ID</th><th>Название</th><th>Код</th><th>Действия</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in allCourses" :key="c.id">
              <td>{{ c.id }}</td>
              <td>{{ c.fullname }}</td>
              <td>{{ c.shortname }}</td>
              <td class="row-actions">
                <button class="btn-secondary" @click="openBuilder(c)">Конструктор</button>
                <button class="btn-secondary" @click="runSeed(c.id)">Seed</button>
                <button class="btn-danger" @click="removeCourse(c.id)">Удалить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Course Builder Modal -->
    <div v-if="builderCourse" class="modal-overlay" @click.self="closeBuilder">
      <div class="modal">
        <div class="modal-header">
          <h3>Конструктор курса: {{ builderCourse.fullname }}</h3>
          <button class="close-btn" @click="closeBuilder">×</button>
        </div>
        <div class="modal-body">
          <div class="builder-panels">
            <div class="builder-left">
              <h4>Содержимое курса</h4>
              <p v-if="builderLoading" class="loading">Загрузка...</p>
              <div v-else>
                <div v-for="sec in builderSections" :key="sec.id" class="builder-section">
                  <div class="sec-header">
                    <strong>{{ sec.name || 'Раздел ' + sec.section }}</strong>
                    <button class="btn-text-danger" @click="removeSection(sec.id)">Удалить раздел</button>
                  </div>
                  <div class="sec-modules">
                    <div v-for="mod in sec.modules" :key="mod.id || mod.cmid" class="builder-mod">
                      <span>{{ mod.name }} <small>({{ mod.modname }})</small></span>
                      <button class="btn-text-danger" @click="removeModule(mod.id || mod.cmid)">Удалить</button>
                    </div>
                    <div v-if="!sec.modules || sec.modules.length === 0" class="empty">Нет модулей</div>
                  </div>
                </div>
                <div v-if="builderSections.length === 0" class="empty">Нет разделов</div>
              </div>
            </div>
            <div class="builder-right">
              <h4>Добавить раздел</h4>
              <form class="mini-form" @submit.prevent="handleAddSection">
                <input v-model="newSection.name" type="text" placeholder="Название раздела" required />
                <textarea v-model="newSection.summary" placeholder="Описание" rows="2"></textarea>
                <button type="submit" class="btn-primary">Добавить раздел</button>
              </form>

              <h4 style="margin-top:18px">Добавить модуль</h4>
              <form class="mini-form" @submit.prevent="handleAddModule">
                <select v-model="newModule.section_num" required>
                  <option value="" disabled>Выберите раздел</option>
                  <option v-for="sec in builderSections" :key="sec.id" :value="sec.section">{{ sec.name || 'Раздел ' + sec.section }}</option>
                </select>
                <select v-model="newModule.modname" required>
                  <option value="" disabled>Тип модуля</option>
                  <option value="page">Страница</option>
                  <option value="url">Ссылка</option>
                  <option value="forum">Форум</option>
                  <option value="quiz">Тест</option>
                  <option value="assign">Задание</option>
                  <option value="label">Ярлык</option>
                </select>
                <input v-model="newModule.name" type="text" placeholder="Название модуля" required />
                <textarea v-if="newModule.modname === 'page' || newModule.modname === 'label'" v-model="newModule.content" placeholder="HTML-содержимое" rows="3"></textarea>
                <input v-if="newModule.modname === 'url'" v-model="newModule.url" type="text" placeholder="https://..." />
                <textarea v-model="newModule.intro" placeholder="Вступление / описание" rows="2"></textarea>
                <button type="submit" class="btn-primary">Добавить модуль</button>
              </form>
              <div v-if="builderMessage" class="message" :class="{ error: builderError }">{{ builderMessage }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  fetchUsers,
  fetchCourses,
  createCourse,
  deleteCourse,
  seedCourse,
  fetchAdminCourseContents,
  createSection,
  deleteSection,
  createModule,
  deleteModule,
} from '@/api/client'

const tab = ref('users')
const users = ref([])
const allCourses = ref([])
const loading = ref(true)
const coursesLoading = ref(true)
const courseMessage = ref('')
const newCourse = ref({ fullname: '', shortname: '', summary: '' })

const builderCourse = ref(null)
const builderSections = ref([])
const builderLoading = ref(false)
const builderMessage = ref('')
const builderError = ref(false)
const newSection = ref({ name: '', summary: '' })
const newModule = ref({ section_num: '', modname: '', name: '', content: '', url: '', intro: '' })

onMounted(async () => {
  try {
    const data = await fetchUsers()
    users.value = data.users || []
  } catch (e) {
    console.error('Failed to load users', e)
  } finally {
    loading.value = false
  }
  loadCourses()
})

async function loadCourses() {
  coursesLoading.value = true
  try {
    const data = await fetchCourses()
    allCourses.value = (data.courses || []).filter(c => c.id !== 1)
  } catch (e) {
    console.error('Failed to load courses', e)
  } finally {
    coursesLoading.value = false
  }
}

async function handleCreateCourse() {
  courseMessage.value = ''
  try {
    await createCourse(newCourse.value)
    courseMessage.value = 'Курс создан!'
    newCourse.value = { fullname: '', shortname: '', summary: '' }
    await loadCourses()
  } catch (e) {
    courseMessage.value = 'Ошибка создания курса.'
  }
}

async function removeCourse(courseId) {
  if (!confirm('Удалить курс? Это необратимо.')) return
  try {
    await deleteCourse(courseId)
    await loadCourses()
  } catch (e) {
    alert('Ошибка удаления курса')
  }
}

async function runSeed(courseId) {
  if (!confirm('Заполнить курс демо-контентом? Существующий контент будет очищен.')) return
  try {
    await seedCourse(courseId)
    alert('Курс успешно заполнен демо-контентом')
  } catch (e) {
    alert('Ошибка seed: ' + e.message)
  }
}

async function openBuilder(course) {
  builderCourse.value = course
  builderMessage.value = ''
  await loadBuilderContents()
}

function closeBuilder() {
  builderCourse.value = null
  builderSections.value = []
}

async function loadBuilderContents() {
  if (!builderCourse.value) return
  builderLoading.value = true
  try {
    const data = await fetchAdminCourseContents(builderCourse.value.id)
    builderSections.value = data.sections || []
  } catch (e) {
    console.error('Failed to load builder contents', e)
  } finally {
    builderLoading.value = false
  }
}

async function handleAddSection() {
  builderMessage.value = ''
  builderError.value = false
  try {
    await createSection(builderCourse.value.id, { name: newSection.value.name, summary: newSection.value.summary })
    newSection.value = { name: '', summary: '' }
    await loadBuilderContents()
  } catch (e) {
    builderMessage.value = 'Ошибка добавления раздела'
    builderError.value = true
  }
}

async function handleAddModule() {
  builderMessage.value = ''
  builderError.value = false
  try {
    const payload = {
      section_num: Number(newModule.value.section_num),
      modname: newModule.value.modname,
      name: newModule.value.name,
      intro: newModule.value.intro,
      content: newModule.value.content,
      url: newModule.value.url,
    }
    await createModule(builderCourse.value.id, payload)
    newModule.value = { section_num: '', modname: '', name: '', content: '', url: '', intro: '' }
    await loadBuilderContents()
  } catch (e) {
    builderMessage.value = 'Ошибка добавления модуля'
    builderError.value = true
  }
}

async function removeSection(sectionId) {
  if (!confirm('Удалить раздел и все его модули?')) return
  try {
    await deleteSection(builderCourse.value.id, sectionId)
    await loadBuilderContents()
  } catch (e) {
    alert('Ошибка удаления раздела')
  }
}

async function removeModule(cmid) {
  if (!confirm('Удалить модуль?')) return
  try {
    await deleteModule(builderCourse.value.id, cmid)
    await loadBuilderContents()
  } catch (e) {
    alert('Ошибка удаления модуля')
  }
}
</script>

<style scoped>
.admin { padding: 60px 0; background: var(--color-bg-light); min-height: 60vh; }
.admin h2 { text-align: center; font-size: 36px; color: var(--color-dark); margin-bottom: 24px; }
.tabs { display: flex; justify-content: center; gap: 12px; margin-bottom: 24px; }
.tabs button { padding: 10px 20px; border: none; background: #e5e7eb; border-radius: 6px; cursor: pointer; }
.tabs button.active { background: var(--color-primary); color: #fff; }
.tab-content { background: #fff; padding: 24px; border-radius: 12px; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 10px; border-bottom: 1px solid #eee; text-align: left; }
.create-form { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.create-form input, .create-form textarea { flex: 1; min-width: 180px; padding: 8px; border: 1px solid #ddd; border-radius: 6px; }
.row-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-danger { background: #ef4444; color: #fff; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
.btn-secondary { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
.btn-text-danger { background: transparent; color: #ef4444; border: none; cursor: pointer; font-size: 13px; }
.message { margin-bottom: 12px; font-size: 13px; color: green; }
.message.error { color: #ef4444; }
.loading { color: #6b7280; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.45); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 20px; }
.modal { background: #fff; border-radius: 12px; width: 100%; max-width: 900px; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #eee; }
.close-btn { background: none; border: none; font-size: 24px; cursor: pointer; }
.modal-body { overflow: auto; padding: 16px 20px; }
.builder-panels { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 720px) { .builder-panels { grid-template-columns: 1fr; } }
.builder-left, .builder-right { background: #f9fafb; border-radius: 10px; padding: 14px; }
.builder-section { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; margin-bottom: 10px; }
.sec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.sec-modules { padding-left: 8px; }
.builder-mod { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #f3f4f6; }
.empty { color: #9ca3af; font-size: 13px; padding: 6px 0; }
.mini-form { display: flex; flex-direction: column; gap: 8px; }
.mini-form input, .mini-form textarea, .mini-form select { padding: 8px; border: 1px solid #ddd; border-radius: 6px; }
</style>
