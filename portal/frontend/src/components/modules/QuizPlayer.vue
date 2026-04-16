<template>
  <div class="quiz-player">
    <div v-if="noQuestions" class="quiz-empty">
      <p>В этом тесте пока нет вопросов.</p>
    </div>
    <div v-else-if="!attemptId" class="quiz-start">
      <div v-if="data.intro" class="quiz-intro" v-html="sanitized(data.intro)"></div>
      <p>Готовы начать тест?</p>
      <button class="btn-primary" @click="start" :disabled="starting">{{ starting ? 'Загрузка...' : 'Начать тест' }}</button>
    </div>

    <div v-else-if="reviewData" class="quiz-review">
      <h4>Результат</h4>
      <div v-if="hasReviewScore" class="review-score">Балл: {{ reviewData.grade || reviewData.mark }} / {{ reviewData.grade?.maxgrade || quizMeta.sumgrades }}</div>
      <div v-else class="review-score">Тест завершён</div>
      <div v-for="q in reviewData.questions" :key="q.slot" class="review-question">
        <div v-html="sanitized(q.html)"></div>
      </div>
      <button class="btn-secondary" @click="reset">Закрыть результат</button>
    </div>

    <div v-else-if="questions.length" class="quiz-attempt">
      <div class="attempt-header">
        <span>Вопрос {{ currentIndex + 1 }} из {{ questions.length }}</span>
      </div>

      <QuestionRenderer
        :question="questions[currentIndex]"
        :modelValue="answers[questions[currentIndex].slot]"
        @update="(slot, val) => updateAnswer(slot, val)"
        @updateMatch="(slot, code, val) => updateMatch(slot, code, val)"
      />

      <div class="attempt-nav">
        <button class="btn-secondary" :disabled="currentIndex === 0" @click="currentIndex--">Назад</button>
        <button v-if="currentIndex < questions.length - 1" class="btn-primary" @click="currentIndex++">Далее</button>
        <button v-else class="btn-primary finish" @click="finish" :disabled="finishing">{{ finishing ? 'Завершение...' : 'Завершить тест' }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { startQuiz, fetchQuizAttempt, saveQuizAttempt, finishQuizAttempt, fetchQuizReview, markModuleComplete } from '@/api/client.js'
import QuestionRenderer from './QuestionRenderer.vue'

const props = defineProps({
  data: { type: Object, required: true }
})

const emit = defineEmits(['finished'])

const attemptId = ref(null)
const attemptUniqueId = ref(null)
const starting = ref(false)
const finishing = ref(false)
const noQuestions = ref(false)
const questions = ref([])
const currentIndex = ref(0)
const answers = ref({})
const reviewData = ref(null)
const quizMeta = ref({})

const hasReviewScore = computed(() => {
  return reviewData.value && (reviewData.value.grade != null || reviewData.value.mark != null)
})

async function start() {
  starting.value = true
  noQuestions.value = false
  try {
    const res = await startQuiz(props.data.course_id, props.data.cmid)
    attemptId.value = res.attempt?.id
    if (attemptId.value) {
      await loadAttempt(attemptId.value)
    }
  } catch (e) {
    if (e.response?.status === 400 || e.message?.includes('нет вопросов')) {
      noQuestions.value = true
    } else {
      alert('Не удалось начать тест: ' + e.message)
    }
  } finally {
    starting.value = false
  }
}

async function loadAttempt(id) {
  try {
    const res = await fetchQuizAttempt(props.data.course_id, props.data.cmid, id, 0)
    quizMeta.value = res.quizinfo || {}
    attemptUniqueId.value = res.attempt?.uniqueid || null
    questions.value = normalizeQuestions(res.questions || [])
    currentIndex.value = 0
  } catch (e) {
    alert('Ошибка загрузки теста: ' + e.message)
  }
}

function normalizeQuestions(raw) {
  if (!raw || !raw.length) return []
  return raw.map(q => {
    const html = q.html || ''
    const parser = new DOMParser()
    const doc = parser.parseFromString(html, 'text/html')
    const root = doc.body.querySelector('.que')
    const typeClass = root ? Array.from(root.classList).find(c =>
      ['multichoice', 'truefalse', 'match', 'shortanswer', 'essay', 'numerical'].includes(c)
    ) : 'unknown'
    const type = typeClass || 'unknown'

    const qtextEl = doc.querySelector('.qtext')
    const questiontext = qtextEl ? qtextEl.innerHTML : ''

    const out = {
      slot: q.slot,
      type,
      questiontext,
      answers: [],
      stems: [],
      options: [],
      single: true,
    }

    if (type === 'multichoice' || type === 'truefalse') {
      const answerDiv = doc.querySelector('.answer')
      if (answerDiv) {
        const rows = answerDiv.querySelectorAll(':scope > div')
        let hasCheckbox = false
        let hasRadio = false
        rows.forEach(row => {
          const input = row.querySelector('input[type="radio"], input[type="checkbox"]')
          if (!input) return
          if (input.type === 'checkbox') hasCheckbox = true
          if (input.type === 'radio') hasRadio = true
          if (input.value === '-1') return // skip "clear choice"
          let text = ''
          const labelDiv = row.querySelector('[data-region="answer-label"]')
          if (labelDiv) {
            const clone = labelDiv.cloneNode(true)
            const numSpan = clone.querySelector('.answernumber')
            if (numSpan) numSpan.remove()
            text = clone.textContent.trim()
          } else {
            const label = row.querySelector('label')
            if (label) text = label.textContent.trim()
          }
          out.answers.push({ id: input.value, text })
        })
        out.single = hasRadio && !hasCheckbox
      }
    }

    if (type === 'match') {
      const table = doc.querySelector('table.answer')
      if (table) {
        table.querySelectorAll('tr').forEach((tr, idx) => {
          const textTd = tr.querySelector('td.text')
          const select = tr.querySelector('select')
          if (textTd && select) {
            out.stems.push({ code: String(idx), text: textTd.textContent.trim() })
          }
        })
        const firstSelect = table.querySelector('select')
        if (firstSelect) {
          firstSelect.querySelectorAll('option').forEach(opt => {
            if (opt.value !== '') {
              out.options.push({ value: opt.value, label: opt.textContent.trim() })
            }
          })
        }
      }
    }

    return out
  })
}

function updateAnswer(slot, val) {
  answers.value[slot] = val
  autoSave()
}

function updateMatch(slot, code, val) {
  if (!answers.value[slot] || typeof answers.value[slot] !== 'object') {
    answers.value[slot] = {}
  }
  answers.value[slot][code] = val
  autoSave()
}

let saveTimeout = null
function autoSave() {
  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    doSave()
  }, 1500)
}

async function doSave() {
  if (!attemptId.value) return
  const payload = buildSavePayload()
  try {
    await saveQuizAttempt(props.data.course_id, props.data.cmid, attemptId.value, payload)
  } catch (e) {
    console.error('Auto-save failed', e)
  }
}

function buildSavePayload() {
  const dataSeq = []
  const uid = attemptUniqueId.value
  if (!uid) return dataSeq
  questions.value.forEach(q => {
    const val = answers.value[q.slot]
    const prefix = `q${uid}:${q.slot}`
    if (q.type === 'multichoice' || q.type === 'truefalse') {
      if (Array.isArray(val)) {
        val.forEach(v => {
          dataSeq.push({ name: `${prefix}_choice${v}`, value: 1, slot: q.slot })
        })
      } else if (val !== undefined && val !== null && val !== '') {
        dataSeq.push({ name: `${prefix}_answer`, value: String(val), slot: q.slot })
      }
    } else if (q.type === 'match') {
      if (val && typeof val === 'object') {
        Object.entries(val).forEach(([code, v]) => {
          if (v !== undefined && v !== null && v !== '') {
            dataSeq.push({ name: `${prefix}_sub${code}`, value: String(v), slot: q.slot })
          }
        })
      }
    } else {
      if (val !== undefined && val !== null && val !== '') {
        dataSeq.push({ name: `${prefix}_answer`, value: String(val), slot: q.slot })
      }
    }
  })
  return dataSeq
}

async function finish() {
  finishing.value = true
  try {
    await doSave()
    await finishQuizAttempt(props.data.course_id, props.data.cmid, attemptId.value)
    try {
      const review = await fetchQuizReview(props.data.course_id, props.data.cmid, attemptId.value)
      reviewData.value = review
    } catch (reviewErr) {
      console.warn('Review not available', reviewErr)
      reviewData.value = { grade: null, mark: null, questions: [] }
    }
    try {
      await markModuleComplete(props.data.course_id, props.data.cmid)
    } catch (compErr) {
      console.warn('Failed to mark module complete', compErr)
    }
    emit('finished')
  } catch (e) {
    alert('Ошибка завершения: ' + e.message)
  } finally {
    finishing.value = false
  }
}

function reset() {
  attemptId.value = null
  attemptUniqueId.value = null
  noQuestions.value = false
  questions.value = []
  answers.value = {}
  reviewData.value = null
  currentIndex.value = 0
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
.quiz-player { }
.quiz-start { display: flex; flex-direction: column; gap: 10px; }
.quiz-empty { color: #6b7280; font-size: 14px; }
.quiz-intro { margin-bottom: 12px; line-height: 1.5; color: #374151; }
.btn-primary { background: var(--color-primary); color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.6; }
.btn-secondary { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
.attempt-header { font-size: 13px; color: #6b7280; margin-bottom: 10px; }
.attempt-nav { display: flex; gap: 10px; margin-top: 16px; }
.finish { background: #dc2626; }
.quiz-review { }
.review-score { font-size: 18px; font-weight: 600; margin-bottom: 12px; }
.review-question { padding: 10px; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 10px; background: #fff; }
</style>
