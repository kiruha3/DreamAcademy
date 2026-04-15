<template>
  <div class="question-renderer">
    <div class="q-text" v-html="sanitized(question.questiontext)"></div>

    <!-- multichoice / truefalse -->
    <div v-if="question.type === 'multichoice' || question.type === 'truefalse'" class="q-answers">
      <label v-for="ans in question.answers" :key="ans.id" class="answer-row">
        <input
          :type="question.single ? 'radio' : 'checkbox'"
          :name="'q_' + question.slot"
          :value="ans.id"
          :checked="isSelected(ans.id)"
          @change="handleChange(ans.id, $event)"
        />
        <span v-html="sanitized(ans.text)"></span>
      </label>
    </div>

    <!-- shortanswer / numerical -->
    <div v-else-if="question.type === 'shortanswer' || question.type === 'numerical'" class="q-answers">
      <input
        type="text"
        class="short-input"
        :value="currentValue"
        @input="emit('update', question.slot, $event.target.value)"
        placeholder="Ваш ответ"
      />
    </div>

    <!-- match -->
    <div v-else-if="question.type === 'match'" class="q-answers">
      <div v-for="stem in question.stems" :key="stem.code" class="match-row">
        <span v-html="sanitized(stem.text)"></span>
        <select :value="matchValue(stem.code)" @change="emit('updateMatch', question.slot, stem.code, $event.target.value)">
          <option value="" disabled>Выберите...</option>
          <option v-for="opt in question.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>
    </div>

    <!-- essay -->
    <div v-else-if="question.type === 'essay'" class="q-answers">
      <textarea
        rows="4"
        class="essay-input"
        :value="currentValue"
        @input="emit('update', question.slot, $event.target.value)"
        placeholder="Введите развёрнутый ответ"
      ></textarea>
    </div>

    <div v-else class="unsupported">Тип вопроса «{{ question.type }}» пока не поддерживается в портале.</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  question: { type: Object, required: true },
  modelValue: { type: [String, Array, Object], default: '' }
})

const emit = defineEmits(['update', 'updateMatch'])

const currentValue = computed(() => {
  if (Array.isArray(props.modelValue)) return props.modelValue.join(',')
  if (typeof props.modelValue === 'object' && props.modelValue !== null) return ''
  return props.modelValue || ''
})

function isSelected(ansId) {
  if (Array.isArray(props.modelValue)) return props.modelValue.includes(String(ansId))
  return String(props.modelValue) === String(ansId)
}

function handleChange(ansId, event) {
  const isCheckbox = event.target.type === 'checkbox'
  if (isCheckbox) {
    const arr = Array.isArray(props.modelValue) ? [...props.modelValue] : []
    const s = String(ansId)
    if (event.target.checked) {
      if (!arr.includes(s)) arr.push(s)
    } else {
      const idx = arr.indexOf(s)
      if (idx !== -1) arr.splice(idx, 1)
    }
    emit('update', props.question.slot, arr)
  } else {
    emit('update', props.question.slot, String(ansId))
  }
}

function matchValue(stemCode) {
  const v = props.modelValue
  if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
    return v[stemCode] || ''
  }
  return ''
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
.question-renderer { margin-bottom: 20px; }
.q-text { font-weight: 500; margin-bottom: 10px; }
.q-answers { display: flex; flex-direction: column; gap: 8px; }
.answer-row { display: flex; align-items: flex-start; gap: 8px; cursor: pointer; padding: 8px; border-radius: 6px; }
.answer-row:hover { background: #f3f4f6; }
.short-input, .essay-input { width: 100%; max-width: 400px; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; }
.match-row { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.unsupported { color: #9ca3af; font-size: 13px; }
</style>
