<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/api/client'

const router = useRouter()
const auth = useAuthStore()

const name = ref('')
const email = ref('')
const password = ref('')
const error = ref<string | null>(null)
const loading = ref(false)

async function onSubmit() {
  error.value = null
  loading.value = true
  try {
    const created = await auth.register(name.value, email.value, password.value)
    await router.push({
      name: 'signin',
      query: {
        registered: '1',
        email: email.value,
        name: name.value,
        ...(created.email_verified ? {} : { verify: '1' }),
      },
    })
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : e instanceof Error ? e.message : 'Could not register'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <RouterLink class="back cc-link" to="/">← Home</RouterLink>
    <div class="panel cc-card">
      <h1 class="title cc-display">Create your space</h1>
      <p class="subtitle">A few details — then you can shape your profile before chatting.</p>

      <form class="form" @submit.prevent="onSubmit">
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <div>
          <label class="cc-label" for="name">Name</label>
          <input id="name" v-model="name" class="cc-input" type="text" autocomplete="name" required />
        </div>
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
            autocomplete="new-password"
            minlength="8"
            required
          />
          <p class="hint">At least 8 characters (max 512).</p>
        </div>
        <button class="cc-btn cc-btn--primary submit" type="submit" :disabled="loading">
          {{ loading ? 'Creating…' : 'Create account' }}
        </button>
      </form>

      <p class="foot">
        Already have an account?
        <RouterLink class="cc-link" to="/signin">Sign in</RouterLink>
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
  background: linear-gradient(195deg, #f0ebe4 0%, var(--color-canvas) 45%, #ecf2ee 100%);
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

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.hint {
  margin: 0.35rem 0 0;
  font-size: 0.8125rem;
  color: var(--color-ink-faint);
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
