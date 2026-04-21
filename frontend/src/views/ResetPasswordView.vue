<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/api/client'

const route = useRoute()
const auth = useAuthStore()

const token = ref('')
const userId = ref('')
const password = ref('')
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const loading = ref(false)

onMounted(() => {
  const t = route.query.token
  const u = route.query.user_id
  if (typeof t === 'string') token.value = t
  if (typeof u === 'string') userId.value = u
})

async function onSubmit() {
  error.value = null
  success.value = null
  if (!token.value.trim() || !userId.value.trim()) {
    error.value = 'Invalid reset link. Request a new reset email from the sign-in page.'
    return
  }
  loading.value = true
  try {
    const res = await auth.resetPassword(token.value.trim(), userId.value.trim(), password.value)
    success.value = res.detail
  } catch (e) {
    error.value =
      e instanceof ApiError ? e.detail : e instanceof Error ? e.message : 'Could not reset password.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <RouterLink class="back cc-link" to="/">← Home</RouterLink>
    <div class="panel cc-card">
      <h1 class="title cc-display">Set a new password</h1>
      <p class="subtitle">Choose a password you have not used here before.</p>

      <form class="form" @submit.prevent="onSubmit">
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <p v-if="success" class="success" role="status">{{ success }}</p>

        <div v-if="!success">
          <label class="cc-label" for="password">New password</label>
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

        <button v-if="!success" class="cc-btn cc-btn--primary submit" type="submit" :disabled="loading">
          {{ loading ? 'Updating…' : 'Update password' }}
        </button>
      </form>

      <p class="foot">
        <RouterLink class="cc-link" to="/signin">Back to sign in</RouterLink>
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
  margin-bottom: 1.5rem;
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

.success {
  margin: 0;
  padding: 0.65rem 0.85rem;
  border-radius: var(--radius-sm);
  background: rgba(40, 120, 70, 0.1);
  color: #1f5c36;
  font-size: 0.9375rem;
}

.submit {
  margin-top: 0.25rem;
}

.foot {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9375rem;
}
</style>
