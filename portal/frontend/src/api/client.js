const API_BASE = import.meta.env.VITE_API_URL || ''

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

async function apiPost(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function fetchCourses() {
  return apiGet('/api/courses')
}

export function inviteToCourse(courseId, data) {
  return apiPost(`/api/courses/${courseId}/invite`, data)
}
