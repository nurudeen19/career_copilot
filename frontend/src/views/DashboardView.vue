<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'

import ChatPanel from '@/components/dashboard/ChatPanel.vue'
import ProfileModal from '@/components/dashboard/ProfileModal.vue'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'

const router = useRouter()
const auth = useAuthStore()
const profile = useProfileStore()

const modalOpen = ref(false)

const displayName = computed(() => auth.user?.name || 'there')

function openProfile() {
  modalOpen.value = true
}

function closeModal() {
  modalOpen.value = false
}

async function onProfileSaved() {
  await profile.fetchProfile()
}

function onNeedProfile() {
  modalOpen.value = true
}

function logout() {
  profile.clear()
  auth.logout()
  void router.push({ name: 'landing' })
}

onMounted(async () => {
  await profile.fetchProfile()
})
</script>

<template>
  <div class="dash">
    <header class="top">
      <div class="top-inner cc-container">
        <div class="brand">
          <RouterLink to="/" class="logo cc-display">Career Copilot</RouterLink>
          <span class="hi">Hi, {{ displayName }}</span>
        </div>
        <div class="actions">
          <span v-if="!profile.complete" class="pill">Profile incomplete</span>
          <button type="button" class="cc-btn cc-btn--ghost" @click="openProfile">Edit profile</button>
          <button type="button" class="cc-btn cc-btn--ghost" @click="logout">Sign out</button>
        </div>
      </div>
    </header>

    <div class="body">
      <div class="body-inner cc-container">
        <aside class="insight">
          <p class="insight-kicker">Today</p>
          <p class="insight-lead cc-display">One calm place to think through your next move.</p>
          <p class="insight-copy">
            Ask about transitions, compensation signals, skill gaps, or how to frame your story — we keep the thread
            here so you can iterate without losing context.
          </p>
          <p v-if="!profile.complete" class="insight-note">
            We’ll ask for role, goal, and location before the first exchange so guidance stays grounded.
          </p>
        </aside>

        <div class="chat-stage">
          <ChatPanel :profile-complete="profile.complete" @need-profile="onNeedProfile" />
        </div>
      </div>
    </div>

    <ProfileModal :open="modalOpen" @close="closeModal" @saved="onProfileSaved" />
  </div>
</template>

<style scoped>
.dash {
  min-height: 100dvh;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(120% 80% at 100% 0%, rgba(61, 107, 92, 0.08), transparent 55%),
    radial-gradient(90% 60% at 0% 100%, rgba(198, 125, 78, 0.06), transparent 50%),
    var(--color-canvas);
}

.top {
  flex-shrink: 0;
  border-bottom: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(10px);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.6) inset;
}

.top-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 1rem;
  padding-bottom: 1rem;
}

.brand {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.logo {
  font-size: 1.15rem;
  color: var(--color-ink);
  text-decoration: none;
}

.logo:hover {
  color: var(--color-accent);
}

.hi {
  font-size: 0.875rem;
  color: var(--color-ink-muted);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.pill {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.28rem 0.65rem;
  border-radius: var(--radius-full);
  background: rgba(198, 125, 78, 0.14);
  color: #6b442a;
}

.body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.body-inner {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-top: 1rem;
  padding-bottom: 0;
}

@media (min-width: 900px) {
  .body-inner {
    flex-direction: row;
    align-items: stretch;
    gap: 1.5rem;
    padding-top: 1.25rem;
  }
}

.insight {
  flex-shrink: 0;
  padding: 0.5rem 0 0;
  max-width: 32rem;
}

@media (min-width: 900px) {
  .insight {
    width: min(280px, 32%);
    padding-top: 0.35rem;
  }
}

.insight-kicker {
  margin: 0 0 0.35rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.insight-lead {
  margin: 0 0 0.6rem;
  font-size: 1.35rem;
  line-height: 1.25;
  color: var(--color-ink);
}

.insight-copy {
  margin: 0 0 0.85rem;
  font-size: 0.9rem;
  color: var(--color-ink-muted);
  line-height: 1.6;
}

.insight-note {
  margin: 0;
  padding: 0.75rem 0.9rem;
  font-size: 0.85rem;
  line-height: 1.5;
  border-radius: var(--radius-md);
  background: rgba(61, 107, 92, 0.09);
  color: var(--color-accent-hover);
  border: 1px solid rgba(61, 107, 92, 0.12);
}

.chat-stage {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
</style>
