<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h3>Пригласить на курс</h3>
      <form @submit.prevent="submit">
        <input v-model="form.email" type="email" placeholder="Email" required />
        <input v-model="form.firstname" type="text" placeholder="Имя" />
        <input v-model="form.lastname" type="text" placeholder="Фамилия" />
        <select v-model="form.role">
          <option value="student">Студент</option>
          <option value="teacher">Преподаватель</option>
          <option value="course_creator">Создатель курса</option>
        </select>
        <div class="actions">
          <button type="button" class="btn-secondary" @click="$emit('close')">Отмена</button>
          <button type="submit" class="btn-primary">Пригласить</button>
        </div>
        <div v-if="message" class="message">{{ message }}</div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { inviteToCourse } from '@/api/client'

const props = defineProps({ courseId: { type: Number, required: true } })
const emit = defineEmits(['close', 'invited'])

const form = ref({ email: '', firstname: '', lastname: '', role: 'student' })
const message = ref('')

async function submit() {
  message.value = ''
  try {
    await inviteToCourse(props.courseId, form.value)
    message.value = 'Приглашение отправлено!'
    emit('invited')
    setTimeout(() => emit('close'), 1000)
  } catch (e) {
    message.value = 'Ошибка приглашения. Проверьте права доступа.'
  }
}
</script>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; padding: 24px; border-radius: 12px; width: 360px; max-width: 90%; }
.modal h3 { margin-bottom: 16px; }
.modal input, .modal select { display: block; width: 100%; margin-bottom: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 6px; }
.actions { display: flex; gap: 10px; margin-top: 10px; }
.actions button { flex: 1; }
.btn-secondary { background: #e5e7eb; color: #374151; border: none; padding: 10px; border-radius: 6px; cursor: pointer; }
.message { margin-top: 10px; font-size: 13px; color: green; }
</style>
