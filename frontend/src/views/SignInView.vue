<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/api/client'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref<string | null>(null)
const loading = ref(false)
const welcome = ref<string | null>(null)

onMounted(() => {
  if (!auth.isAuthenticated) auth.persistUser(null)
  const q = route.query
  if (q.registered === '1' && typeof q.name === 'string') {
    welcome.value = `Thanks, ${q.name}. You can sign in whenever you’re ready.`
  }
  if (typeof q.email === 'string') email.value = q.email
})

async function onSubmit() {
  error.value = null
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    const next = typeof route.query.next === 'string' ? route.query.next : '/dashboard'
    await router.push(next || '/dashboard')
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : e instanceof Error ? e.message : 'Sign in failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <RouterLink class="back cc-link" to="/">← Home</RouterLink>
    <div class="panel cc-card">
      <h1 class="title cc-display">Welcome back</h1>
      <p class="subtitle">Sign in to continue your conversation.</p>
      <p v-if="welcome" class="welcome">{{ welcome }}</p>

      <form class="form" @submit.prevent="onSubmit">
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <div>
          <label class="cc-label" for="email">Email</label>
          <input id="email" v-model="email" class="cc-input" type="email" autocomplete="email" required />
        </div>
        <div>
          <label class="cc-label" for="password">Password</label>
          <input
            id="password"
            v-model="password"
            class="cc-input"
            type="password"
            autocomplete="current-password"
            required
          />
        </div>
        <button class="cc-btn cc-btn--primary submit" type="submit" :disabled="loading">
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <p class="foot">
        New here?
        <RouterLink class="cc-link" to="/signup">Create an account</RouterLink>
      </p>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.25rem;
  background: linear-gradient(165deg, #eef4f0 0%, var(--color-canvas) 42%, #f7f1ea 100%);
}

.back {
  align-self: flex-start;
  margin-bottom: 1.5rem;
}

.panel {
  width: 100%;
  max-width: 400px;
  padding: 2rem 1.75rem;
}

.title {
  font-size: 1.75rem;
  margin-bottom: 0.35rem;
}

.subtitle {
  color: var(--color-ink-muted);
  font-size: 0.9375rem;
  margin-bottom: 1.75rem;
}

.welcome {
  margin: -0.5rem 0 1.25rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  background: rgba(61, 107, 92, 0.1);
  color: var(--color-accent-hover);
  font-size: 0.9rem;
  line-height: 1.45;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.error {
  margin: 0;
  padding: 0.65rem 0.85rem;
  border-radius: var(--radius-sm);
  background: rgba(180, 60, 50, 0.08);
  color: #8b2e22;
  font-size: 0.875rem;
}

.submit {
  margin-top: 0.25rem;
}

.foot {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9375rem;
  color: var(--color-ink-muted);
}
</style>
