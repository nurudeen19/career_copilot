import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { apiFetch, ApiError, setStoredToken, getStoredToken } from '@/api/client'
import type { LoginResponse, User } from '@/types/models'

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

  /** True when the user has a verified email and may use the app (dashboard, API). */
  const canUseApp = computed(() => Boolean(token.value && user.value?.email_verified === true))

  /** Legacy: token present (may still be pending verification). Prefer ``canUseApp`` for gating. */
  const isAuthenticated = computed(() => Boolean(token.value))

  function setToken(t: string | null) {
    token.value = t
    setStoredToken(t)
  }

  /**
   * Refresh user from ``GET /auth/me`` when the session may be stale or missing ``email_verified``.
   * Clears the session on 401/403 (e.g. unverified account or invalid token).
   */
  async function hydrateUserIfNeeded() {
    if (!token.value) return
    if (user.value?.email_verified === true) return
    try {
      const me = await apiFetch<User>('/auth/me')
      persistUser(me)
    } catch (e) {
      if (e instanceof ApiError && (e.status === 401 || e.status === 403)) {
        logout()
      }
    }
  }

  async function register(name: string, email: string, password: string): Promise<User> {
    return apiFetch<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
      skipAuth: true,
    })
  }

  async function login(email: string, password: string): Promise<void> {
    const res = await apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      skipAuth: true,
    })
    setToken(res.access_token)
    persistUser(res.user)
  }

  async function resendVerification(email: string): Promise<void> {
    await apiFetch<{ detail: string }>('/auth/resend-verification', {
      method: 'POST',
      body: JSON.stringify({ email }),
      skipAuth: true,
    })
  }

  async function verifyEmail(token: string, userId: string): Promise<{ detail: string }> {
    return apiFetch<{ detail: string }>('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token, user_id: userId }),
      skipAuth: true,
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
    canUseApp,
    register,
    login,
    logout,
    resendVerification,
    verifyEmail,
    setToken,
    persistUser,
    loadUserFromStorage,
    hydrateUserIfNeeded,
  }
})
