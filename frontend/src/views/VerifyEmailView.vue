<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, RouterLink } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/api/client'

const route = useRoute()
const auth = useAuthStore()

const status = ref<'pending' | 'ok' | 'error'>('pending')
const message = ref<string | null>(null)
const started = ref(false)

onMounted(async () => {
  if (started.value) return
  started.value = true

  const token = route.query.token
  const userId = route.query.user_id
  if (typeof token !== 'string' || typeof userId !== 'string' || !token.trim() || !userId.trim()) {
    status.value = 'error'
    message.value = 'This link is missing verification details. Use the link from your email or request a new one.'
    return
  }

  try {
    const res = await auth.verifyEmail(token.trim(), userId.trim())
    status.value = 'ok'
    message.value = res.detail
  } catch (e) {
    status.value = 'error'
    message.value =
      e instanceof ApiError ? e.detail : e instanceof Error ? e.message : 'Verification failed.'
  }
})
</script>

<template>
  <div class="page">
    <RouterLink class="back cc-link" to="/">← Home</RouterLink>
    <div class="panel cc-card">
      <h1 class="title cc-display">Email verification</h1>

      <p v-if="status === 'pending'" class="subtitle">Confirming your address…</p>
      <p v-else-if="status === 'ok'" class="success" role="status">{{ message }}</p>
      <p v-else class="error" role="alert">{{ message }}</p>

      <p v-if="status !== 'pending'" class="foot">
        <RouterLink class="cc-btn cc-btn--primary" to="/signin">Sign in</RouterLink>
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
  max-width: 420px;
  padding: 2rem 1.75rem;
}

.title {
  font-size: 1.75rem;
  margin-bottom: 0.75rem;
}

.subtitle {
  color: var(--color-ink-muted);
  font-size: 0.9375rem;
  margin: 0;
}

.success {
  margin: 0;
  padding: 0.65rem 0.85rem;
  border-radius: var(--radius-sm);
  background: rgba(40, 120, 70, 0.1);
  color: #1f5c36;
  font-size: 0.9375rem;
}

.error {
  margin: 0;
  padding: 0.65rem 0.85rem;
  border-radius: var(--radius-sm);
  background: rgba(180, 60, 50, 0.08);
  color: #8b2e22;
  font-size: 0.875rem;
}

.foot {
  margin-top: 1.5rem;
}

.foot :deep(.cc-btn) {
  display: inline-block;
  text-align: center;
  text-decoration: none;
}
</style>
