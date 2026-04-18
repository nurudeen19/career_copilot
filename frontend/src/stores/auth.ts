import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { apiFetch, setStoredToken, getStoredToken } from '@/api/client'
import { decodeJwtSub } from '@/utils/jwt'
import type { User } from '@/types/models'

const USER_KEY = 'career_copilot_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getStoredToken())
  const user = ref<User | null>(null)

  function loadUserFromStorage() {
    try {
      const raw = localStorage.getItem(USER_KEY)
      if (raw) user.value = JSON.parse(raw) as User
    } catch {
      user.value = null
    }
  }

  function persistUser(u: User | null) {
    if (u) localStorage.setItem(USER_KEY, JSON.stringify(u))
    else localStorage.removeItem(USER_KEY)
    user.value = u
  }

  const isAuthenticated = computed(() => Boolean(token.value))

  function setToken(t: string | null) {
    token.value = t
    setStoredToken(t)
  }

  async function register(name: string, email: string, password: string): Promise<User> {
    return apiFetch<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
      skipAuth: true,
    })
  }

  async function login(email: string, password: string): Promise<void> {
    const res = await apiFetch<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      skipAuth: true,
    })
    setToken(res.access_token)
    const sub = decodeJwtSub(res.access_token)
    persistUser({
      id: sub ?? '',
      name: email.split('@')[0] ?? 'You',
      email: email.toLowerCase().trim(),
      created_at: new Date().toISOString(),
    })
  }

  function logout() {
    sessionStorage.removeItem('career_copilot_thread_id')
    setToken(null)
    persistUser(null)
  }

  loadUserFromStorage()
  if (!token.value) persistUser(null)

  return {
    token,
    user,
    isAuthenticated,
    register,
    login,
    logout,
    setToken,
    persistUser,
    loadUserFromStorage,
  }
})
