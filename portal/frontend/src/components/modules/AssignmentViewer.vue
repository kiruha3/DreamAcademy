<template>
  <div class="assignment-viewer">
    <div v-if="loading" class="loading">Загрузка задания...</div>
    <div v-else>
      <div v-if="status.intro" class="assign-intro" v-html="sanitized(status.intro)"></div>
      <div class="assign-meta">
        <span v-if="status.duedate">Дедлайн: {{ formatDate(status.duedate) }}</span>
        <span v-if="status.grade">Макс. оценка: {{ status.grade }}</span>
        <span class="status-badge" :class="status.status">{{ statusLabel(status.status) }}</span>
      </div>

      <div v-if="status.status === 'graded'" class="grade-box">
        <div class="grade-value">Оценка: {{ status.local_grade }} / {{ status.grade }}</div>
        <div v-if="status.feedback" class="grade-feedback">Комментарий: {{ status.feedback }}</div>
      </div>

      <div v-if="isStudent" class="upload-section">
        <div v-if="status.file_name" class="current-file">
          Загружен файл: <strong>{{ status.file_name }}</strong>
        </div>
        <label class="file-input-label">
          <input type="file" @change="handleFileChange" />
          <span class="btn-upload">{{ status.file_name ? 'Заменить файл' : 'Загрузить файл' }}</span>
        </label>
        <button v-if="selectedFile" class="btn-submit" @click="submitFile" :disabled="uploading">
          {{ uploading ? 'Отправка...' : 'Отправить' }}
        </button>
      </div>

      <!-- Teacher grading view -->
      <div v-else class="teacher-section">
        <p class="hint">Вы можете проверить работы студентов в панели администратора.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchAssignStatus, submitAssignment } from '@/api/client.js'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  data: { type: Object, required: true }
})

const authStore = useAuthStore()
const isStudent = computed(() => authStore.user?.role === 'student')

const status = ref({})
const loading = ref(true)
const selectedFile = ref(null)
const uploading = ref(false)

onMounted(async () => {
  await loadStatus()
})

async function loadStatus() {
  try {
    status.value = await fetchAssignStatus(props.data.course_id, props.data.cmid)
  } catch (e) {
    console.error('Failed to load assignment status', e)
  } finally {
    loading.value = false
  }
}

function handleFileChange(e) {
  selectedFile.value = e.target.files[0] || null
}

async function submitFile() {
  if (!selectedFile.value) return
  uploading.value = true
  try {
    await submitAssignment(props.data.course_id, props.data.cmid, selectedFile.value)
    selectedFile.value = null
    await loadStatus()
  } catch (e) {
    alert('Ошибка отправки: ' + e.message)
  } finally {
    uploading.value = false
  }
}

function formatDate(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  return d.toLocaleDateString('ru-RU') + ' ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

function statusLabel(s) {
  const map = {
    not_submitted: 'Не сдано',
    submitted: 'Сдано',
    graded: 'Оценено',
  }
  return map[s] || s
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
.assignment-viewer { }
.assign-intro { margin-bottom: 12px; line-height: 1.5; }
.assign-meta { display: flex; gap: 12px; flex-wrap: wrap; font-size: 13px; color: #6b7280; margin-bottom: 12px; }
.status-badge { padding: 2px 8px; border-radius: 999px; font-size: 12px; background: #e5e7eb; color: #374151; }
.status-badge.submitted { background: #dbeafe; color: #1e40af; }
.status-badge.graded { background: #dcfce7; color: #166534; }
.grade-box { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 10px 12px; border-radius: 8px; margin-bottom: 12px; }
.grade-value { font-weight: 600; color: #166534; }
.grade-feedback { font-size: 13px; color: #374151; margin-top: 4px; }
.upload-section { margin-top: 12px; }
.current-file { font-size: 13px; margin-bottom: 8px; }
.file-input-label { display: inline-flex; cursor: pointer; }
.file-input-label input { display: none; }
.btn-upload { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; padding: 6px 12px; border-radius: 6px; }
.btn-submit { background: var(--color-primary); color: #fff; border: none; padding: 6px 14px; border-radius: 6px; margin-left: 8px; cursor: pointer; }
.btn-submit:disabled { opacity: 0.6; }
.teacher-section { margin-top: 10px; }
.hint { font-size: 13px; color: #6b7280; }
.loading { color: #6b7280; }
</style>
