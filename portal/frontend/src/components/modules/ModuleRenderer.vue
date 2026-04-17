<template>
  <div class="module-renderer">
    <component :is="viewerComponent" :data="moduleData" @finished="onFinished" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import PageViewer from './PageViewer.vue'
import LabelViewer from './LabelViewer.vue'
import UrlViewer from './UrlViewer.vue'
import GenericViewer from './GenericViewer.vue'
import AssignmentViewer from './AssignmentViewer.vue'
import QuizPlayer from './QuizPlayer.vue'
import ForumViewer from './ForumViewer.vue'
import BookViewer from './BookViewer.vue'
import ScormViewer from './ScormViewer.vue'

const props = defineProps({
  data: { type: Object, required: true }
})

const viewerComponent = computed(() => {
  switch (props.data.modname) {
    case 'page': return PageViewer
    case 'label': return LabelViewer
    case 'url': return UrlViewer
    case 'assign': return AssignmentViewer
    case 'quiz': return QuizPlayer
    case 'forum': return ForumViewer
    case 'book': return BookViewer
    case 'scorm': return ScormViewer
    default: return GenericViewer
  }
})

const moduleData = computed(() => props.data)

const emit = defineEmits(['moduleFinished'])
function onFinished() {
  emit('moduleFinished')
}
</script>

<style scoped>
.module-renderer { width: 100%; }
</style>
