<template>
  <div class="scorm-viewer">
    <div v-if="detail.intro" class="scorm-intro" v-html="sanitized(detail.intro)"></div>
    <div v-else class="scorm-intro">Интерактивный обучающий модуль (SCORM)</div>
    <button class="scorm-link" @click="openModal">
      Открыть SCORM →
    </button>

    <!-- Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ detail.name || 'SCORM' }}</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <div class="modal-body">
          <iframe
            v-if="scormUrl"
            :src="scormUrl"
            width="100%"
            height="100%"
            frameborder="0"
            allowfullscreen
          ></iframe>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchModuleDetail, markModuleComplete } from '@/api/client.js'

const props = defineProps({
  data: { type: Object, required: true }
})

const emit = defineEmits(['finished'])

const detail = ref({ ...props.data })
const showModal = ref(false)

const scormUrl = computed(() => {
  if (!props.data.cmid) return ''
  return `http://185.112.226.84:62080/mod/scorm/view.php?id=${props.data.cmid}`
})

onMounted(async () => {
  try {
    const res = await fetchModuleDetail(props.data.course_id, props.data.cmid)
    detail.value = { ...detail.value, ...res }
  } catch (e) {
    console.error('Failed to load scorm detail', e)
  }
  try {
    await markModuleComplete(props.data.course_id, props.data.cmid)
    emit('finished')
  } catch (e) {
    console.error('Failed to mark scorm complete', e)
  }
})

function openModal() {
  showModal.value = true
}

function closeModal() {
  showModal.value = false
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
.scorm-viewer { display: flex; flex-direction: column; gap: 10px; }
.scorm-link { display: inline-flex; align-items: center; gap: 6px; color: #fff; background: var(--color-primary); padding: 10px 16px; border-radius: 8px; text-decoration: none; border: none; cursor: pointer; width: fit-content; font-size: 14px; font-weight: 500; }
.scorm-link:hover { opacity: 0.92; }
.scorm-intro { margin: 0 0 4px; color: #374151; font-size: 14px; line-height: 1.5; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; z-index: 200; padding: 16px; }
.modal { background: #fff; border-radius: 12px; width: 100%; max-width: 1100px; height: 90vh; overflow: hidden; display: flex; flex-direction: column; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; border-bottom: 1px solid #eee; }
.modal-header h3 { margin: 0; font-size: 16px; }
.close-btn { background: none; border: none; font-size: 26px; line-height: 1; cursor: pointer; color: #6b7280; }
.close-btn:hover { color: #111827; }
.modal-body { flex: 1; overflow: hidden; padding: 0; }
.modal-body iframe { display: block; }
</style>
