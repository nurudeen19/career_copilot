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
    <header class="top cc-container">
      <div class="brand">
        <RouterLink to="/" class="logo cc-display">Career Copilot</RouterLink>
        <span class="hi">Hi, {{ displayName }}</span>
      </div>
      <div class="actions">
        <span v-if="!profile.complete" class="pill">Profile incomplete</span>
        <button type="button" class="cc-btn cc-btn--ghost" @click="openProfile">Edit profile</button>
        <button type="button" class="cc-btn cc-btn--ghost" @click="logout">Sign out</button>
      </div>
    </header>

    <main class="main cc-container">
      <aside class="aside">
        <p class="aside-title cc-display">Today</p>
        <p class="aside-copy">
          Ask about transitions, compensation signals, skill gaps, or how to frame your story — we’ll keep the thread
          here.
        </p>
        <p v-if="!profile.complete" class="aside-note">
          We’ll ask for your role, goal, and location before the first real exchange — it keeps guidance grounded.
        </p>
      </aside>
      <ChatPanel class="chat-wrap" :profile-complete="profile.complete" @need-profile="onNeedProfile" />
    </main>

    <ProfileModal :open="modalOpen" @close="closeModal" @saved="onProfileSaved" />
  </div>
</template>

<style scoped>
.dash {
  min-height: 100vh;
  background: var(--color-canvas);
  display: flex;
  flex-direction: column;
}

.top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(8px);
}

.brand {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.logo {
  font-size: 1.2rem;
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
  padding: 0.25rem 0.6rem;
  border-radius: var(--radius-full);
  background: rgba(198, 125, 78, 0.15);
  color: #6b442a;
}

.main {
  flex: 1;
  display: grid;
  gap: 1.5rem;
  padding-top: 1.5rem;
  padding-bottom: 2rem;
  grid-template-columns: 1fr;
  align-items: start;
}

@media (min-width: 900px) {
  .main {
    grid-template-columns: minmax(200px, 260px) 1fr;
  }
}

.aside {
  padding: 0.25rem 0;
}

.aside-title {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}

.aside-copy,
.aside-note {
  font-size: 0.9rem;
  color: var(--color-ink-muted);
  line-height: 1.55;
  margin: 0 0 0.75rem;
}

.aside-note {
  padding: 0.75rem;
  border-radius: var(--radius-md);
  background: rgba(61, 107, 92, 0.08);
  color: var(--color-accent-hover);
}

.chat-wrap {
  min-width: 0;
}
</style>
