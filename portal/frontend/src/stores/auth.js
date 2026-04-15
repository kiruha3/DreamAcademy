import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, register, fetchMe } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  async function signIn(email, password) {
    const data = await login(email, password)
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    return data
  }

  async function signUp(payload) {
    const data = await register(payload)
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    return data
  }

  async function loadUser() {
    if (!token.value) return
    try {
      const data = await fetchMe()
      user.value = data
    } catch (e) {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isAuthenticated,
    signIn,
    signUp,
    loadUser,
    logout,
  }
})
