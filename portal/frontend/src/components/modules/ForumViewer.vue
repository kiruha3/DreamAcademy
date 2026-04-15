<template>
  <div class="forum-viewer">
    <div v-if="loading" class="loading">Загрузка форума...</div>
    <div v-else>
      <div class="forum-actions">
        <button class="btn-primary" @click="showNewTopic = !showNewTopic">
          {{ showNewTopic ? 'Отмена' : 'Новая тема' }}
        </button>
      </div>

      <div v-if="showNewTopic" class="new-topic-form">
        <input v-model="newTopicSubject" type="text" placeholder="Тема" />
        <textarea v-model="newTopicMessage" rows="3" placeholder="Сообщение"></textarea>
        <button class="btn-primary" @click="createTopic" :disabled="sending || !newTopicSubject.trim()">
          {{ sending ? 'Создание...' : 'Создать тему' }}
        </button>
      </div>

      <div v-if="activeDiscussion" class="discussion-view">
        <button class="btn-back" @click="activeDiscussion = null">← Назад к списку тем</button>
        <h4>{{ activeDiscussion.name }}</h4>
        <ForumDiscussion :courseId="data.course_id" :cmid="data.cmid" :discussionId="activeDiscussion.id" />
      </div>

      <div v-else class="discussions-list">
        <div v-for="d in discussions" :key="d.id" class="discussion-item" @click="openDiscussion(d)">
          <div class="discussion-title">{{ d.name }}</div>
          <div class="discussion-meta">
            Автор: {{ d.userfullname || 'Неизвестно' }} • Ответов: {{ d.numreplies || 0 }}
          </div>
        </div>
        <div v-if="!discussions.length" class="empty">Нет обсуждений</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchForumDiscussions, createForumDiscussion } from '@/api/client.js'
import ForumDiscussion from './ForumDiscussion.vue'

const props = defineProps({
  data: { type: Object, required: true }
})

const discussions = ref([])
const loading = ref(true)
const activeDiscussion = ref(null)
const showNewTopic = ref(false)
const newTopicSubject = ref('')
const newTopicMessage = ref('')
const sending = ref(false)

onMounted(async () => {
  await loadDiscussions()
})

async function loadDiscussions() {
  try {
    const res = await fetchForumDiscussions(props.data.course_id, props.data.cmid)
    discussions.value = res.discussions || []
  } catch (e) {
    console.error('Failed to load discussions', e)
  } finally {
    loading.value = false
  }
}

function openDiscussion(d) {
  activeDiscussion.value = d
}

async function createTopic() {
  sending.value = true
  try {
    await createForumDiscussion(props.data.course_id, props.data.cmid, newTopicSubject.value, newTopicMessage.value)
    newTopicSubject.value = ''
    newTopicMessage.value = ''
    showNewTopic.value = false
    await loadDiscussions()
  } catch (e) {
    alert('Ошибка создания темы: ' + e.message)
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.forum-viewer { }
.forum-actions { margin-bottom: 10px; }
.btn-primary { background: var(--color-primary); color: #fff; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.6; }
.new-topic-form { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.new-topic-form input, .new-topic-form textarea { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; }
.discussions-list { display: flex; flex-direction: column; gap: 8px; }
.discussion-item { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; cursor: pointer; }
.discussion-item:hover { border-color: var(--color-primary); }
.discussion-title { font-weight: 500; }
.discussion-meta { font-size: 12px; color: #6b7280; margin-top: 4px; }
.empty { color: #9ca3af; font-size: 13px; }
.discussion-view { }
.btn-back { background: transparent; border: none; color: var(--color-primary); cursor: pointer; margin-bottom: 8px; }
.loading { color: #6b7280; }
</style>
