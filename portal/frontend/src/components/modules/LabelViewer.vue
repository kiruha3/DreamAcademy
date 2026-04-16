<template>
  <div class="label-viewer" v-html="sanitized(detail.intro || detail.content)"></div>
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
    console.error('Failed to load label detail', e)
  }
  try {
    await markModuleComplete(props.data.course_id, props.data.cmid)
    emit('finished')
  } catch (e) {
    console.error('Failed to mark label complete', e)
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
.label-viewer :deep(p) { margin: 0; }
.label-viewer :deep(.alert) { padding: 10px 14px; border-radius: 8px; background: #e0f2fe; color: #0c4a6e; }
.label-viewer :deep(img) { max-width: 100%; height: auto; }
</style>
