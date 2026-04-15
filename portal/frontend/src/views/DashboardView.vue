<template>
  <section class="dashboard">
    <div class="container">
      <h2>Личный кабинет</h2>
      <div class="dashboard-grid">
        <div class="card">
          <h3>Мои курсы</h3>
          <p v-if="coursesLoading">Загрузка...</p>
          <ul v-else-if="myCourses.length">
            <li v-for="course in myCourses" :key="course.id">
              <router-link :to="`/courses/${course.id}`">{{ course.fullname }}</router-link>
            </li>
          </ul>
          <p v-else>Вы пока не записаны ни на один курс.</p>
        </div>
        <div class="card">
          <h3>Прогресс</h3>
          <p>Пройдено 0 из 0 модулей.</p>
        </div>
        <div class="card">
          <h3>Тесты</h3>
          <p>Нет активных проверочных работ.</p>
        </div>
        <div class="card moodle-card">
          <h3>Доступ к Moodle</h3>
          <div v-if="moodleCreds">
            <p><strong>Ссылка:</strong> <a :href="moodleCreds.moodle_url" target="_blank">{{ moodleCreds.moodle_url }}</a></p>
            <p><strong>Логин Moodle:</strong> {{ moodleCreds.username }}</p>
            <p class="hint">{{ moodleCreds.note }}</p>
          </div>
          <div v-else>
            <p>Загрузка...</p>
          </div>
        </div>
        <div class="card password-card">
          <h3>Сменить пароль</h3>
          <form @submit.prevent="handleChangePassword">
            <input v-model="currentPassword" type="password" placeholder="Текущий пароль" required />
            <input v-model="newPassword" type="password" placeholder="Новый пароль" required />
            <button type="submit" class="btn-primary">Сменить</button>
          </form>
          <div v-if="passwordMessage" class="message">{{ passwordMessage }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchMoodleCredentials, changePassword, fetchMyCourses } from '@/api/client'

const moodleCreds = ref(null)
const currentPassword = ref('')
const newPassword = ref('')
const passwordMessage = ref('')
const myCourses = ref([])
const coursesLoading = ref(true)

onMounted(async () => {
  try {
    moodleCreds.value = await fetchMoodleCredentials()
  } catch (e) {
    console.error('Failed to load Moodle credentials', e)
  }
  try {
    const data = await fetchMyCourses()
    myCourses.value = data.courses || []
  } catch (e) {
    console.error('Failed to load my courses', e)
  } finally {
    coursesLoading.value = false
  }
})

async function handleChangePassword() {
  passwordMessage.value = ''
  try {
    await changePassword(currentPassword.value, newPassword.value)
    passwordMessage.value = 'Пароль успешно изменён! Он также обновлён в Moodle.'
    currentPassword.value = ''
    newPassword.value = ''
  } catch (e) {
    passwordMessage.value = 'Ошибка: проверьте текущий пароль.'
  }
}
</script>

<style scoped>
.dashboard { padding: 60px 0; background: var(--color-bg-light); min-height: 60vh; }
.dashboard h2 { text-align: center; font-size: 36px; color: var(--color-dark); margin-bottom: 48px; }
.dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 24px; }
.card { background: #fff; padding: 24px; border-radius: 12px; }
.card h3 { color: var(--color-dark); margin-bottom: 8px; }
.moodle-card a { color: var(--color-primary); }
.hint { font-size: 13px; color: #666; margin-top: 8px; }
.password-card input { display: block; width: 100%; margin-bottom: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 6px; }
.password-card button { width: 100%; }
.message { margin-top: 10px; font-size: 13px; color: green; }
.card ul { list-style: none; padding: 0; }
.card li { margin-bottom: 8px; }
.card li a { color: var(--color-primary); text-decoration: none; }
.card li a:hover { text-decoration: underline; }
</style>
