import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { apiFetch } from '@/api/client'
import type { Profile, ProfilePatch } from '@/types/models'
import { isProfileComplete } from '@/utils/profile'

export const useProfileStore = defineStore('profile', () => {
  const profile = ref<Profile | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const complete = computed(() => isProfileComplete(profile.value))

  async function fetchProfile() {
    loading.value = true
    error.value = null
    try {
      profile.value = await apiFetch<Profile>('/profile')
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Could not load profile'
      profile.value = null
    } finally {
      loading.value = false
    }
  }

  async function saveProfile(patch: ProfilePatch): Promise<void> {
    loading.value = true
    error.value = null
    try {
      profile.value = await apiFetch<Profile>('/profile', {
        method: 'PATCH',
        body: JSON.stringify(patch),
      })
    } finally {
      loading.value = false
    }
  }

  function clear() {
    profile.value = null
    error.value = null
  }

  return { profile, loading, error, complete, fetchProfile, saveProfile, clear }
})
