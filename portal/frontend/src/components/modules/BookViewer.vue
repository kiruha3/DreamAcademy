<template>
  <div class="book-viewer">
    <div v-if="loading" class="loading">Загрузка книги...</div>
    <div v-else class="book-layout">
      <aside class="book-toc">
        <div class="toc-title">Оглавление</div>
        <ul>
          <li
            v-for="(ch, idx) in chapters"
            :key="ch.id"
            :class="{ active: currentIndex === idx }"
            @click="currentIndex = idx"
          >
            {{ ch.title }}
          </li>
        </ul>
      </aside>
      <article class="book-content">
        <div v-if="currentChapter" class="chapter">
          <h3 class="chapter-title">{{ currentChapter.title }}</h3>
          <div class="chapter-body" v-html="sanitized(currentChapter.content)"></div>
        </div>
        <div class="chapter-nav">
          <button
            class="nav-btn"
            :disabled="currentIndex <= 0"
            @click="currentIndex--"
          >
            ← Назад
          </button>
          <button
            class="nav-btn"
            :disabled="currentIndex >= chapters.length - 1"
            @click="currentIndex++"
          >
            Вперед →
          </button>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchBookChapters, markModuleComplete } from '@/api/client.js'

const props = defineProps({
  data: { type: Object, required: true }
})

const emit = defineEmits(['finished'])

const chapters = ref([])
const currentIndex = ref(0)
const loading = ref(true)

const currentChapter = computed(() => chapters.value[currentIndex.value] || null)

onMounted(async () => {
  try {
    const data = await fetchBookChapters(props.data.course_id, props.data.cmid)
    chapters.value = data.chapters || []
  } catch (e) {
    console.error('Failed to load book chapters', e)
  } finally {
    loading.value = false
  }
  try {
    await markModuleComplete(props.data.course_id, props.data.cmid)
    emit('finished')
  } catch (e) {
    console.error('Failed to mark book complete', e)
  }
})

function sanitized(html) {
  if (!html) return ''
  const allowed = /<(\/?)(b|i|em|strong|u|p|br|hr|h[1-6]|ul|ol|li|div|span|a|img|table|thead|tbody|tr|td|th|blockquote|pre|code|sup|sub)(\s+[^>]*)?>/gi
  return html.replace(/<[^>]+>/g, (tag) => {
    return allowed.test(tag) ? tag : ''
  })
}
</script>

<style scoped>
.book-viewer {
  color: var(--color-text);
}
.loading {
  color: #6b7280;
  padding: 20px 0;
}
.book-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 20px;
}
@media (max-width: 720px) {
  .book-layout {
    grid-template-columns: 1fr;
  }
  .book-toc {
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 12px;
  }
}
.book-toc {
  border-right: 1px solid #e5e7eb;
  padding-right: 12px;
}
.toc-title {
  font-weight: 600;
  color: var(--color-dark);
  margin-bottom: 10px;
  font-size: 14px;
}
.book-toc ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.book-toc li {
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #374151;
  margin-bottom: 4px;
}
.book-toc li:hover {
  background: #f3f4f6;
}
.book-toc li.active {
  background: #e0f2fe;
  color: #0c4a6e;
  font-weight: 500;
}
.book-content {
  min-width: 0;
}
.chapter {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 18px;
}
.chapter-title {
  font-size: 18px;
  color: var(--color-dark);
  margin-bottom: 12px;
  font-weight: 600;
}
.chapter-body {
  font-size: 14px;
  line-height: 1.7;
}
.chapter-body :deep(h1),
.chapter-body :deep(h2),
.chapter-body :deep(h3),
.chapter-body :deep(h4) {
  color: var(--color-dark);
  margin-top: 16px;
  margin-bottom: 8px;
}
.chapter-body :deep(p) {
  margin-bottom: 10px;
}
.chapter-body :deep(ul),
.chapter-body :deep(ol) {
  padding-left: 20px;
  margin-bottom: 10px;
}
.chapter-body :deep(li) {
  margin-bottom: 4px;
}
.chapter-body :deep(pre) {
  background: #f4f6f8;
  border: 1px solid #e8ecf0;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  white-space: pre-wrap;
  font-size: 13px;
  margin-bottom: 10px;
}
.chapter-body :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: #eef1f4;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.chapter-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}
.chapter-body :deep(a) {
  color: var(--color-primary);
  text-decoration: none;
}
.chapter-body :deep(a:hover) {
  text-decoration: underline;
}
.chapter-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
  font-size: 13px;
}
.chapter-body :deep(th),
.chapter-body :deep(td) {
  border: 1px solid #e2e4ea;
  padding: 8px;
  text-align: left;
}
.chapter-body :deep(th) {
  background: #f8f9fb;
}
.chapter-nav {
  display: flex;
  justify-content: space-between;
  margin-top: 14px;
}
.nav-btn {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.nav-btn:hover {
  background: #e5e7eb;
}
.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
