<template>
  <div class="module-renderer">
    <component :is="viewerComponent" :data="moduleData" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import PageViewer from './PageViewer.vue'
import LabelViewer from './LabelViewer.vue'
import UrlViewer from './UrlViewer.vue'
import GenericViewer from './GenericViewer.vue'

const props = defineProps({
  data: { type: Object, required: true }
})

const viewerComponent = computed(() => {
  switch (props.data.modname) {
    case 'page': return PageViewer
    case 'label': return LabelViewer
    case 'url': return UrlViewer
    default: return GenericViewer
  }
})

const moduleData = computed(() => props.data)
</script>

<style scoped>
.module-renderer { width: 100%; }
</style>
