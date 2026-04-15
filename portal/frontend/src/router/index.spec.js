import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

// Import the route definitions (we'll recreate router to inject fresh pinia)
const routes = [
  { path: '/', name: 'Home', component: { template: '<div>Home</div>' } },
  { path: '/login', name: 'Login', component: { template: '<div>Login</div>' }, meta: { guestOnly: true } },
  { path: '/dashboard', name: 'Dashboard', component: { template: '<div>Dashboard</div>' }, meta: { requiresAuth: true } },
  { path: '/admin', name: 'Admin', component: { template: '<div>Admin</div>' }, meta: { requiresAuth: true, roles: ['admin', 'teacher', 'course_creator'] } },
]

describe('Router guards', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    })
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('redirects unauthenticated user from /dashboard to /login', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    router.beforeEach((to, from, next) => {
      const authStore = useAuthStore()
      if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        return next('/login')
      }
      if (to.meta.guestOnly && authStore.isAuthenticated) {
        return next('/dashboard')
      }
      if (to.meta.roles && (!authStore.user || !to.meta.roles.includes(authStore.user.role))) {
        return next('/')
      }
      next()
    })

    await router.push('/dashboard')
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('allows authenticated user to /dashboard', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    router.beforeEach((to, from, next) => {
      const authStore = useAuthStore()
      if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        return next('/login')
      }
      if (to.meta.guestOnly && authStore.isAuthenticated) {
        return next('/dashboard')
      }
      if (to.meta.roles && (!authStore.user || !to.meta.roles.includes(authStore.user.role))) {
        return next('/')
      }
      next()
    })

    const authStore = useAuthStore()
    authStore.token = 'fake-token'

    await router.push('/dashboard')
    expect(router.currentRoute.value.path).toBe('/dashboard')
  })

  it('redirects student from /admin to /', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    router.beforeEach((to, from, next) => {
      const authStore = useAuthStore()
      if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        return next('/login')
      }
      if (to.meta.guestOnly && authStore.isAuthenticated) {
        return next('/dashboard')
      }
      if (to.meta.roles && (!authStore.user || !to.meta.roles.includes(authStore.user.role))) {
        return next('/')
      }
      next()
    })

    const authStore = useAuthStore()
    authStore.token = 'fake-token'
    authStore.user = { role: 'student' }

    await router.push('/admin')
    expect(router.currentRoute.value.path).toBe('/')
  })
})
