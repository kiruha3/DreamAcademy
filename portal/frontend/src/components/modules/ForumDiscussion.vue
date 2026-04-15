<template>
  <div class="forum-discussion">
    <div class="posts">
      <div v-for="post in posts" :key="post.id" class="post" :class="{ 'post-reply': post.parent !== 0 }">
        <div class="post-header">
          <strong>{{ post.author?.fullname || 'Автор' }}</strong>
          <span class="post-date">{{ formatDate(post.created) }}</span>
        </div>
        <div class="post-message" v-html="sanitized(post.message)"></div>
        <button class="btn-reply" @click="replyTo(post)">Ответить</button>
      </div>
    </div>

    <div class="reply-form">
      <textarea v-model="replyMessage" rows="3" placeholder="Напишите ответ..."></textarea>
      <button class="btn-primary" @click="sendReply" :disabled="!replyMessage.trim() || sending">
        {{ sending ? 'Отправка...' : 'Отправить ответ' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchForumPosts, createForumPost } from '@/api/client.js'

const props = defineProps({
  courseId: { type: [String, Number], required: true },
  cmid: { type: [String, Number], required: true },
  discussionId: { type: [String, Number], required: true }
})

const posts = ref([])
const replyMessage = ref('')
const sending = ref(false)
const replyTarget = ref(null)

onMounted(async () => {
  await loadPosts()
})

async function loadPosts() {
  try {
    const res = await fetchForumPosts(props.courseId, props.cmid, props.discussionId)
    posts.value = res.posts || []
  } catch (e) {
    console.error('Failed to load posts', e)
  }
}

function replyTo(post) {
  replyTarget.value = post
  replyMessage.value = ''
}

async function sendReply() {
  if (!replyMessage.value.trim()) return
  sending.value = true
  try {
    const parentId = replyTarget.value ? replyTarget.value.id : (posts.value[0]?.id || 0)
    await createForumPost(props.courseId, props.cmid, props.discussionId, 'Re:', replyMessage.value, parentId)
    replyMessage.value = ''
    replyTarget.value = null
    await loadPosts()
  } catch (e) {
    alert('Ошибка отправки: ' + e.message)
  } finally {
    sending.value = false
  }
}

function formatDate(ts) {
  if (!ts) return ''
  const d = new Date(ts * 1000)
  return d.toLocaleString('ru-RU')
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
.forum-discussion { }
.posts { display: flex; flex-direction: column; gap: 10px; margin-bottom: 12px; }
.post { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; }
.post-reply { margin-left: 20px; }
.post-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.post-date { font-size: 12px; color: #9ca3af; }
.post-message { font-size: 14px; line-height: 1.4; }
.btn-reply { background: transparent; border: none; color: var(--color-primary); font-size: 12px; cursor: pointer; margin-top: 6px; }
.reply-form { display: flex; flex-direction: column; gap: 8px; }
.reply-form textarea { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; }
.btn-primary { background: var(--color-primary); color: #fff; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; align-self: flex-start; }
.btn-primary:disabled { opacity: 0.6; }
</style>
