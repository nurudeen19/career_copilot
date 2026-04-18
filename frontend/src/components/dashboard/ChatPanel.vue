<script setup lang="ts">
import { ref, watch } from 'vue'

import {
  streamWorkflow,
  extractAssistantTextFromPatch,
  extractValidationError,
} from '@/composables/useWorkflowStream'

export type ChatMessage = { role: 'user' | 'assistant'; content: string }

const props = defineProps<{
  profileComplete: boolean
}>()

const emit = defineEmits<{
  'need-profile': []
}>()

const messages = ref<ChatMessage[]>([
  {
    role: 'assistant',
    content:
      "Hello — I’m here to help you think through your next career move. When you’re ready, share what’s on your mind. " +
      "If you haven’t filled in your profile yet, we’ll gently ask for a few details so our guidance stays personal.",
  },
])

const input = ref('')
const streaming = ref(false)
const threadId = ref<string | null>(null)
const error = ref<string | null>(null)

const THREAD_KEY = 'career_copilot_thread_id'

function loadThread() {
  threadId.value = sessionStorage.getItem(THREAD_KEY)
}

function saveThread(id: string) {
  threadId.value = id
  sessionStorage.setItem(THREAD_KEY, id)
}

watch(
  () => props.profileComplete,
  () => {
    error.value = null
  },
)

loadThread()

async function send() {
  const text = input.value.trim()
  if (!text || streaming.value) return
  if (!props.profileComplete) {
    emit('need-profile')
    return
  }

  error.value = null
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  streaming.value = true

  let draft = ''
  let sawChunk = false

  try {
    for await (const ev of streamWorkflow({
      message: text,
      thread_id: threadId.value,
    })) {
      if (ev.kind === 'step') {
        sawChunk = true
        const { step, patch } = ev
        if (step === 'input_validation') {
          const v = extractValidationError(patch)
          if (v) draft = v
        } else if (step === 'validation_fail') {
          const t = extractAssistantTextFromPatch(patch)
          if (t) draft = t
        } else if (step === 'user_handoff') {
          const h = extractAssistantTextFromPatch(patch)
          if (h) draft = h
        } else if (step === 'synthesizer') {
          const t = extractAssistantTextFromPatch(patch)
          if (t) draft = t
        }
      } else if (ev.kind === 'done') {
        saveThread(ev.thread_id)
        if (draft.trim()) {
          messages.value.push({ role: 'assistant', content: draft.trim() })
        } else if (sawChunk) {
          messages.value.push({
            role: 'assistant',
            content: 'Here’s what I have so far — feel free to ask for more detail on any part.',
          })
        }
        draft = ''
      } else if (ev.kind === 'error') {
        error.value = ev.detail
        messages.value.push({
          role: 'assistant',
          content: `Something went wrong: ${ev.detail}`,
        })
      }
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Request failed'
    error.value = msg
    messages.value.push({ role: 'assistant', content: `Couldn’t complete that request — ${msg}` })
  } finally {
    streaming.value = false
  }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    void send()
  }
}
</script>

<template>
  <section class="chat cc-card">
    <header class="chat-head">
      <h2 class="chat-title cc-display">Conversation</h2>
      <p v-if="!profileComplete" class="hint">Complete your profile to send messages.</p>
    </header>

    <p v-if="error" class="banner" role="status">{{ error }}</p>

    <div class="scroll">
      <div v-for="(m, i) in messages" :key="i" class="row" :class="m.role">
        <div class="bubble">
          {{ m.content }}
        </div>
      </div>
      <div v-if="streaming" class="row assistant">
        <div class="bubble typing">
          <span class="dot" />
          <span class="dot" />
          <span class="dot" />
        </div>
      </div>
    </div>

    <div class="composer">
      <textarea
        v-model="input"
        class="cc-input composer-input"
        rows="2"
        :disabled="streaming"
        placeholder="Share a question or context…"
        aria-label="Message"
        @keydown="onKeydown"
      />
      <button type="button" class="cc-btn cc-btn--primary send" :disabled="streaming" @click="send()">
        Send
      </button>
    </div>
  </section>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  min-height: 420px;
  max-height: min(72vh, 720px);
  overflow: hidden;
}

.chat-head {
  padding: 1rem 1.25rem 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

.chat-title {
  font-size: 1.2rem;
  margin: 0 0 0.25rem;
}

.hint {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-warm);
}

.banner {
  margin: 0;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  background: rgba(198, 125, 78, 0.12);
  color: #7a4a2a;
}

.scroll {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.row {
  display: flex;
}

.row.user {
  justify-content: flex-end;
}

.row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 85%;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-lg);
  font-size: 0.9375rem;
  line-height: 1.55;
  white-space: pre-wrap;
}

.row.user .bubble {
  background: var(--color-accent);
  color: #fff;
  border-bottom-right-radius: var(--radius-sm);
}

.row.assistant .bubble {
  background: var(--color-canvas-2);
  color: var(--color-ink);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: var(--radius-sm);
}

.typing {
  display: flex;
  gap: 0.35rem;
  align-items: center;
  min-width: 4rem;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-ink-faint);
  animation: bounce 1.2s ease infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.15s;
}
.dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.composer {
  display: flex;
  gap: 0.65rem;
  align-items: flex-end;
  padding: 0.85rem 1.25rem 1.1rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}

.composer-input {
  flex: 1;
  resize: none;
}

.send {
  flex-shrink: 0;
}
</style>
