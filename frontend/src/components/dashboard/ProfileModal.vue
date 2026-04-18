<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

import { useProfileStore } from '@/stores/profile'
import type { Profile, ProfilePatch } from '@/types/models'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

const profileStore = useProfileStore()

const form = reactive({
  summary: '',
  profession: '',
  current_salary: '' as string | number,
  salary_target: '' as string | number,
  technologies: '',
  programming_languages: '',
  career_goal: '',
  location: '',
  willing_to_relocate: '' as '' | 'yes' | 'no' | 'unsure',
})

const saving = computed(() => profileStore.loading)

function hydrateFromProfile(p: Profile | null) {
  if (!p) return
  form.summary = p.summary ?? ''
  form.profession = p.profession ?? ''
  form.current_salary = p.current_salary ?? ''
  form.salary_target = p.salary_target ?? ''
  form.technologies = p.technologies ?? ''
  form.programming_languages = p.programming_languages ?? ''
  form.career_goal = p.career_goal ?? ''
  form.location = p.location ?? ''
  if (p.willing_to_relocate === true) form.willing_to_relocate = 'yes'
  else if (p.willing_to_relocate === false) form.willing_to_relocate = 'no'
  else form.willing_to_relocate = 'unsure'
}

watch(
  () => [props.open, profileStore.profile] as const,
  ([isOpen]) => {
    if (isOpen) hydrateFromProfile(profileStore.profile)
  },
  { immediate: true },
)

function numOrNull(v: string | number): number | null {
  if (v === '' || v === null || v === undefined) return null
  const n = typeof v === 'number' ? v : Number(v)
  return Number.isFinite(n) ? n : null
}

function boolOrNull(v: typeof form.willing_to_relocate): boolean | null {
  if (v === 'yes') return true
  if (v === 'no') return false
  return null
}

async function onSave() {
  const patch: ProfilePatch = {
    summary: form.summary.trim() || null,
    profession: form.profession.trim() || null,
    career_goal: form.career_goal.trim() || null,
    location: form.location.trim() || null,
    technologies: form.technologies.trim() || null,
    programming_languages: form.programming_languages.trim() || null,
    current_salary: numOrNull(form.current_salary),
    salary_target: numOrNull(form.salary_target),
    willing_to_relocate: boolOrNull(form.willing_to_relocate),
  }
  await profileStore.saveProfile(patch)
  emit('saved')
  emit('close')
}

function onBackdrop(e: MouseEvent) {
  if ((e.target as HTMLElement).dataset.backdrop === 'true') emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="overlay" data-backdrop="true" role="presentation" @click="onBackdrop">
      <div
        class="modal cc-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="profile-modal-title"
        @click.stop
      >
        <header class="modal-head">
          <h2 id="profile-modal-title" class="title cc-display">Your profile</h2>
          <button type="button" class="icon-close" aria-label="Close" @click="emit('close')">×</button>
        </header>
        <p class="intro">
          A few anchors help us give relevant advice — role, direction, and where you are (or want to be).
        </p>

        <form class="grid" @submit.prevent="onSave">
          <div class="full">
            <label class="cc-label" for="pf-summary">Short summary</label>
            <textarea id="pf-summary" v-model="form.summary" class="cc-input area" rows="3" placeholder="Optional — how you’d describe yourself in a sentence or two" />
          </div>
          <div>
            <label class="cc-label" for="pf-profession">Current role / title</label>
            <input id="pf-profession" v-model="form.profession" class="cc-input" type="text" />
          </div>
          <div>
            <label class="cc-label" for="pf-location">Location</label>
            <input id="pf-location" v-model="form.location" class="cc-input" type="text" placeholder="City, region, or remote" />
          </div>
          <div class="full">
            <label class="cc-label" for="pf-goal">Career goal</label>
            <textarea id="pf-goal" v-model="form.career_goal" class="cc-input area" rows="2" placeholder="What transition or outcome are you exploring?" />
          </div>
          <div>
            <label class="cc-label" for="pf-sal-now">Current salary (annual)</label>
            <input id="pf-sal-now" v-model="form.current_salary" class="cc-input" type="number" min="0" placeholder="Optional" />
          </div>
          <div>
            <label class="cc-label" for="pf-sal-target">Target salary</label>
            <input id="pf-sal-target" v-model="form.salary_target" class="cc-input" type="number" min="0" placeholder="Optional" />
          </div>
          <div class="full">
            <label class="cc-label" for="pf-tech">Technologies & tools</label>
            <input id="pf-tech" v-model="form.technologies" class="cc-input" type="text" placeholder="e.g. Python, AWS, data stacks" />
          </div>
          <div class="full">
            <label class="cc-label" for="pf-lang">Programming languages</label>
            <input id="pf-lang" v-model="form.programming_languages" class="cc-input" type="text" />
          </div>
          <div class="full">
            <label class="cc-label" for="pf-reloc">Open to relocating?</label>
            <select id="pf-reloc" v-model="form.willing_to_relocate" class="cc-input">
              <option value="unsure">Prefer not to say</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>

          <div class="actions full">
            <button type="button" class="cc-btn cc-btn--ghost" @click="emit('close')">Cancel</button>
            <button type="submit" class="cc-btn cc-btn--primary" :disabled="saving">
              {{ saving ? 'Saving…' : 'Save profile' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(26, 23, 20, 0.45);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 1.5rem;
  overflow-y: auto;
}

.modal {
  width: 100%;
  max-width: 520px;
  margin: 2rem auto;
  padding: 1.5rem 1.5rem 1.75rem;
}

.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.title {
  font-size: 1.35rem;
  margin: 0;
}

.icon-close {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  color: var(--color-ink-muted);
  padding: 0.15rem 0.35rem;
}

.icon-close:hover {
  color: var(--color-ink);
}

.intro {
  margin: 0.5rem 0 1.25rem;
  font-size: 0.9rem;
  color: var(--color-ink-muted);
  line-height: 1.5;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem 1rem;
}

.full {
  grid-column: 1 / -1;
}

.area {
  resize: vertical;
  min-height: 4.5rem;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

@media (max-width: 520px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
