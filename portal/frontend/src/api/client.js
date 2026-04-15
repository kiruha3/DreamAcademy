const API_BASE = import.meta.env.VITE_API_URL || ''

function getToken() {
  return localStorage.getItem('token') || ''
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}) },
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function apiPost(path, body, auth = false) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth && getToken()) {
    headers.Authorization = `Bearer ${getToken()}`
  }
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function fetchCourses() {
  return apiGet('/api/courses')
}

export function inviteToCourse(courseId, data) {
  return apiPost(`/api/courses/${courseId}/invite`, data, true)
}

export function login(email, password) {
  return apiPost('/auth/login', { email, password })
}

export function register(data) {
  return apiPost('/auth/register', data)
}

export function fetchMe() {
  return apiGet('/auth/me')
}

export function fetchMoodleCredentials() {
  return apiGet('/auth/moodle-credentials')
}

export function fetchMyCourses() {
  return apiGet('/api/my-courses')
}

export function fetchUsers() {
  return apiGet('/api/admin/users')
}

export function createCourse(data) {
  return apiPost('/api/admin/courses', data, true)
}

export function deleteCourse(courseId) {
  const headers = {}
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`
  return fetch(`${API_BASE}/api/admin/courses/${courseId}`, {
    method: 'DELETE',
    headers,
  }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.status === 204 ? null : r.json() })
}

export function changePassword(current_password, new_password) {
  return apiPost('/auth/change-password', { current_password, new_password }, true)
}

export function fetchCourseContents(courseId) {
  return apiGet(`/api/courses/${courseId}/contents`)
}

export function fetchAdminCourseContents(courseId) {
  return apiGet(`/api/admin/courses/${courseId}/contents`)
}

export function seedCourse(courseId) {
  return apiPost(`/api/admin/courses/${courseId}/seed`, {}, true)
}

export function createSection(courseId, data) {
  return apiPost(`/api/admin/courses/${courseId}/sections`, data, true)
}

export function deleteSection(courseId, sectionId) {
  const headers = {}
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`
  return fetch(`${API_BASE}/api/admin/courses/${courseId}/sections/${sectionId}`, {
    method: 'DELETE',
    headers,
  }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.status === 204 ? null : r.json() })
}

export function createModule(courseId, data) {
  return apiPost(`/api/admin/courses/${courseId}/modules`, data, true)
}

export function deleteModule(courseId, cmid) {
  const headers = {}
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`
  return fetch(`${API_BASE}/api/admin/courses/${courseId}/modules/${cmid}`, {
    method: 'DELETE',
    headers,
  }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.status === 204 ? null : r.json() })
}

export function fetchModuleDetail(courseId, cmid) {
  return apiGet(`/api/courses/${courseId}/modules/${cmid}`)
}

export function markModuleComplete(courseId, cmid) {
  return apiPost(`/api/courses/${courseId}/modules/${cmid}/complete`, {}, true)
}

export function fetchCourseProgress(courseId) {
  return apiGet(`/api/courses/${courseId}/progress`)
}

// Assignment
export function fetchAssignStatus(courseId, cmid) {
  return apiGet(`/api/courses/${courseId}/modules/${cmid}/assign/status`)
}

export function submitAssignment(courseId, cmid, file) {
  const formData = new FormData()
  formData.append('file', file)
  const headers = {}
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`
  return fetch(`${API_BASE}/api/courses/${courseId}/modules/${cmid}/assign/submit`, {
    method: 'POST',
    headers,
    body: formData,
  }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
}

export function fetchAssignSubmissions(courseId, cmid) {
  return apiGet(`/api/courses/${courseId}/modules/${cmid}/assign/submissions`)
}

export function gradeAssignSubmission(courseId, cmid, userId, grade, feedback) {
  return apiPost(`/api/courses/${courseId}/modules/${cmid}/assign/submissions/${userId}/grade`, { grade, feedback }, true)
}

// Quiz
export function startQuiz(courseId, cmid) {
  return apiPost(`/api/courses/${courseId}/modules/${cmid}/quiz/start`, {}, true)
}

export function fetchQuizAttempt(courseId, cmid, attemptId, page = 0) {
  return apiGet(`/api/courses/${courseId}/modules/${cmid}/quiz/attempt/${attemptId}?page=${page}`)
}

export function saveQuizAttempt(courseId, cmid, attemptId, data) {
  return apiPost(`/api/courses/${courseId}/modules/${cmid}/quiz/attempt/${attemptId}/save`, { data }, true)
}

export function finishQuizAttempt(courseId, cmid, attemptId) {
  return apiPost(`/api/courses/${courseId}/modules/${cmid}/quiz/attempt/${attemptId}/finish`, {}, true)
}

export function fetchQuizReview(courseId, cmid, attemptId) {
  return apiGet(`/api/courses/${courseId}/modules/${cmid}/quiz/attempt/${attemptId}/review`)
}

// Forum
export function fetchForumDiscussions(courseId, cmid) {
  return apiGet(`/api/courses/${courseId}/modules/${cmid}/forum/discussions`)
}

export function createForumDiscussion(courseId, cmid, subject, message) {
  return apiPost(`/api/courses/${courseId}/modules/${cmid}/forum/discussions`, { subject, message }, true)
}

export function fetchForumPosts(courseId, cmid, discussionId) {
  return apiGet(`/api/courses/${courseId}/modules/${cmid}/forum/discussions/${discussionId}/posts`)
}

export function createForumPost(courseId, cmid, discussionId, subject, message, parentPostId) {
  return apiPost(`/api/courses/${courseId}/modules/${cmid}/forum/discussions/${discussionId}/posts`, { subject, message, parent_post_id: parentPostId }, true)
}
