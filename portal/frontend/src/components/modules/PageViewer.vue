<template>
  <div class="page-viewer">
    <div v-if="detail.intro" class="page-intro" v-html="sanitized(detail.intro)"></div>
    <div v-if="detail.content" class="page-content" v-html="sanitized(detail.content)"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchModuleDetail, markModuleComplete } from '@/api/client.js'

const props = defineProps({
  data: { type: Object, required: true }
})

const emit = defineEmits(['finished'])

const detail = ref({ ...props.data })

onMounted(async () => {
  try {
    const res = await fetchModuleDetail(props.data.course_id, props.data.cmid)
    detail.value = { ...detail.value, ...res }
  } catch (e) {
    console.error('Failed to load page detail', e)
  }
  try {
    await markModuleComplete(props.data.course_id, props.data.cmid)
    emit('finished')
  } catch (e) {
    console.error('Failed to mark page complete', e)
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
.page-viewer {
  font-size: 15px;
  line-height: 1.65;
  color: var(--color-text);
}
.page-intro {
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  color: #6b7280;
}
.page-content {
  max-width: 100%;
  overflow-wrap: break-word;
  word-break: break-word;
}
.page-content :deep(*) {
  max-width: 100%;
}
.page-content :deep(h1),
.page-content :deep(h2),
.page-content :deep(h3),
.page-content :deep(h4) {
  color: var(--color-dark);
  font-weight: 600;
  line-height: 1.3;
  margin-top: 22px;
  margin-bottom: 10px;
}
.page-content :deep(h1) { font-size: 22px; }
.page-content :deep(h2) { font-size: 19px; }
.page-content :deep(h3) { font-size: 17px; }
.page-content :deep(h4) { font-size: 15px; }
.page-content :deep(p) {
  margin-bottom: 12px;
}
.page-content :deep(ul),
.page-content :deep(ol) {
  padding-left: 22px;
  margin-bottom: 12px;
}
.page-content :deep(li) {
  margin-bottom: 6px;
}
.page-content :deep(a) {
  color: var(--color-primary);
  text-decoration: none;
  word-break: break-word;
}
.page-content :deep(a:hover) {
  text-decoration: underline;
}
.page-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}
.page-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
  display: block;
  overflow-x: auto;
}
.page-content :deep(th),
.page-content :deep(td) {
  border: 1px solid #e2e4ea;
  padding: 10px 12px;
  text-align: left;
}
.page-content :deep(th) {
  background: #f8f9fb;
  color: var(--color-dark);
  font-weight: 600;
}
.page-content :deep(pre) {
  background: #f4f6f8;
  border: 1px solid #e8ecf0;
  color: var(--color-dark);
  padding: 14px;
  border-radius: 10px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 12px;
}
.page-content :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  background: #eef1f4;
  color: #2d3748;
  padding: 2px 6px;
  border-radius: 5px;
  font-size: 13px;
}
.page-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}
.page-content :deep(strong),
.page-content :deep(b) {
  color: var(--color-dark);
  font-weight: 600;
}
.page-content :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  margin: 12px 0;
  padding: 8px 16px;
  background: #f8fafc;
  border-radius: 0 8px 8px 0;
  color: #55647d;
}
.page-content :deep(hr) {
  border: 0;
  border-top: 1px solid #e5e7eb;
  margin: 18px 0;
}
</style>
