<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'

import {
  streamWorkflow,
  extractAssistantTextFromPatch,
  extractValidationError,
} from '@/composables/useWorkflowStream'

export type ChatMessage = { id: string; role: 'user' | 'assistant'; content: string }

const props = defineProps<{
  profileComplete: boolean
}>()

const emit = defineEmits<{
  'need-profile': []
}>()

const composerRef = ref<HTMLTextAreaElement | null>(null)
const scrollRef = ref<HTMLElement | null>(null)

function newMessageId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `m_${Date.now()}_${Math.random().toString(16).slice(2)}`
}

const WELCOME_TEXT =
  "Hello — I’m here to help you think through your next career move. When you’re ready, share what’s on your mind. " +
  "If you haven’t filled in your profile yet, we’ll gently ask for a few details so our guidance stays personal."

function createWelcomeMessages(): ChatMessage[] {
  return [{ id: newMessageId(), role: 'assistant', content: WELCOME_TEXT }]
}

const messages = ref<ChatMessage[]>(createWelcomeMessages())
const input = ref('')
const streaming = ref(false)
const threadId = ref<string | null>(null)
const error = ref<string | null>(null)

/** While waiting for SSE: dots only → rotating lines → live step labels from the graph. */
const STREAM_INTRO_MS = 2800
const STREAM_ROTATE_MS = 2600

const WAITING_LINES = [
  'Planning the next course…',
  'Researching for fresh signals…',
  'Weaving research into a clear story…',
  'Shaping your takeaway…',
] as const

const STEP_CAPTIONS: Record<string, string> = {
  input_validation: 'Checking your message…',
  validation_fail: 'Almost there…',
  planner: 'Planning your next move…',
  research: 'Digging into data and sources…',
  analyst: 'Analyzing what this means for you…',
  critic: 'Stress-testing the take…',
  synthesizer: 'Writing your summary…',
  feedback: 'Incorporating your feedback…',
  user_handoff: 'Finishing up…',
}

type StreamUiPhase = 'intro' | 'rotating' | 'live'
const streamPhase = ref<StreamUiPhase>('intro')
const streamRotateIndex = ref(0)
const streamLiveCaption = ref('')

let streamIntroTimer: ReturnType<typeof setTimeout> | null = null
let streamRotateTimer: ReturnType<typeof setInterval> | null = null

function clearStreamWaitTimers() {
  if (streamIntroTimer !== null) {
    clearTimeout(streamIntroTimer)
    streamIntroTimer = null
  }
  if (streamRotateTimer !== null) {
    clearInterval(streamRotateTimer)
    streamRotateTimer = null
  }
}

function resetStreamUi() {
  clearStreamWaitTimers()
  streamPhase.value = 'intro'
  streamRotateIndex.value = 0
  streamLiveCaption.value = ''
}

function beginStreamWaitUi() {
  resetStreamUi()
  streamPhase.value = 'intro'
  streamIntroTimer = setTimeout(() => {
    if (!streaming.value) return
    streamPhase.value = 'rotating'
    streamRotateIndex.value = 0
    streamRotateTimer = setInterval(() => {
      if (!streaming.value || streamPhase.value !== 'rotating') return
      streamRotateIndex.value = (streamRotateIndex.value + 1) % WAITING_LINES.length
    }, STREAM_ROTATE_MS)
  }, STREAM_INTRO_MS)
}

function onStreamGraphStep(step: string) {
  clearStreamWaitTimers()
  streamPhase.value = 'live'
  streamLiveCaption.value = STEP_CAPTIONS[step] ?? 'Working…'
}

/** Legacy: thread id only (still updated for compatibility). */
const THREAD_KEY = 'career_copilot_thread_id'
/** Full chat UI state: survives same-tab refresh (sessionStorage). */
const CHAT_STATE_KEY = 'career_copilot_chat_state_v1'

type StoredChat = { v?: number; thread_id?: string | null; messages?: unknown[] }

function loadPersistedState() {
  const legacyTid = sessionStorage.getItem(THREAD_KEY)
  if (legacyTid) threadId.value = legacyTid

  const raw = sessionStorage.getItem(CHAT_STATE_KEY)
  if (!raw) {
    messages.value = createWelcomeMessages()
    return
  }
  try {
    const o = JSON.parse(raw) as StoredChat
    if (typeof o.thread_id === 'string' && o.thread_id.trim()) {
      threadId.value = o.thread_id.trim()
      sessionStorage.setItem(THREAD_KEY, threadId.value)
    }
    if (Array.isArray(o.messages) && o.messages.length > 0) {
      const restored: ChatMessage[] = []
      for (const row of o.messages) {
        if (!row || typeof row !== 'object') continue
        const r = row as Record<string, unknown>
        const role = r.role
        const content = r.content
        const id = typeof r.id === 'string' && r.id ? r.id : newMessageId()
        if (role !== 'user' && role !== 'assistant') continue
        if (typeof content !== 'string' || !content.trim()) continue
        restored.push({ id, role, content: content.trim() })
      }
      if (restored.length > 0) {
        messages.value = restored
        return
      }
    }
  } catch {
    /* ignore corrupt storage */
  }
  messages.value = createWelcomeMessages()
}

function clearConversation() {
  if (streaming.value) return
  try {
    sessionStorage.removeItem(CHAT_STATE_KEY)
    sessionStorage.removeItem(THREAD_KEY)
  } catch {
    /* ignore */
  }
  threadId.value = null
  error.value = null
  input.value = ''
  messages.value = createWelcomeMessages()
  void scrollToLatest()
  focusComposer()
}

function persistState() {
  try {
    sessionStorage.setItem(
      CHAT_STATE_KEY,
      JSON.stringify({
        v: 1,
        thread_id: threadId.value,
        messages: messages.value,
      }),
    )
    if (threadId.value) sessionStorage.setItem(THREAD_KEY, threadId.value)
  } catch {
    /* quota / private mode */
  }
}

async function scrollToLatest() {
  await nextTick()
  const el = scrollRef.value
  if (!el) return
  el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
}

function focusComposer() {
  void nextTick(() => {
    const el = composerRef.value
    if (!el || el.disabled) return
    el.focus()
    const len = el.value.length
    el.setSelectionRange(len, len)
  })
}

watch(
  () => props.profileComplete,
  () => {
    error.value = null
  },
)

watch(
  messages,
  () => {
    persistState()
    void scrollToLatest()
  },
  { deep: true },
)
watch(threadId, persistState)

onUnmounted(() => {
  clearStreamWaitTimers()
})

loadPersistedState()
void scrollToLatest()

async function send() {
  const text = input.value.trim()
  if (!text || streaming.value) return
  if (!props.profileComplete) {
    emit('need-profile')
    return
  }

  error.value = null
  messages.value.push({ id: newMessageId(), role: 'user', content: text })
  input.value = ''
  streaming.value = true
  beginStreamWaitUi()
  await scrollToLatest()

  let draft = ''
  let sawChunk = false

  try {
    for await (const ev of streamWorkflow({
      message: text,
      thread_id: threadId.value,
    })) {
      if (ev.kind === 'step') {
        sawChunk = true
        onStreamGraphStep(ev.step)
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
        if (ev.thread_id) {
          threadId.value = ev.thread_id
          sessionStorage.setItem(THREAD_KEY, ev.thread_id)
        }
        if (draft.trim()) {
          messages.value.push({ id: newMessageId(), role: 'assistant', content: draft.trim() })
        } else if (sawChunk) {
          messages.value.push({
            id: newMessageId(),
            role: 'assistant',
            content: 'Here’s what I have so far — feel free to ask for more detail on any part.',
          })
        }
        draft = ''
        await scrollToLatest()
      } else if (ev.kind === 'error') {
        error.value = ev.detail
        messages.value.push({
          id: newMessageId(),
          role: 'assistant',
          content: `Something went wrong: ${ev.detail}`,
        })
        await scrollToLatest()
      }
    }
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Request failed'
    error.value = msg
    messages.value.push({
      id: newMessageId(),
      role: 'assistant',
      content: `Couldn’t complete that request — ${msg}`,
    })
    await scrollToLatest()
  } finally {
    clearStreamWaitTimers()
    resetStreamUi()
    streaming.value = false
    focusComposer()
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
  <section class="chat" aria-label="Career conversation">
    <div class="chat-surface">
      <header class="chat-head">
        <div class="chat-head-text">
          <h2 class="chat-title cc-display">Conversation</h2>
          <p v-if="!profileComplete" class="hint">Complete your profile to send messages.</p>
        </div>
        <button
          type="button"
          class="new-chat cc-btn cc-btn--ghost"
          :disabled="streaming"
          title="Clear this chat and start a new thread on the server"
          @click="clearConversation()"
        >
          New chat
        </button>
      </header>

      <p v-if="error" class="banner" role="status">{{ error }}</p>

      <div ref="scrollRef" class="scroll">
        <div class="scroll-pad">
          <div v-for="m in messages" :key="m.id" class="row" :class="m.role">
            <div class="bubble">
              {{ m.content }}
            </div>
          </div>
          <div v-if="streaming" class="row assistant">
            <div class="bubble typing" :class="{ 'typing--wide': streamPhase !== 'intro' }">
              <div class="typing-dots" aria-hidden="true">
                <span class="dot" />
                <span class="dot" />
                <span class="dot" />
              </div>
              <p
                v-if="streamPhase === 'rotating'"
                :key="streamRotateIndex"
                class="stream-caption"
                aria-live="polite"
              >
                {{ WAITING_LINES[streamRotateIndex] }}
              </p>
              <p v-else-if="streamPhase === 'live' && streamLiveCaption" class="stream-caption" aria-live="polite">
                {{ streamLiveCaption }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="composer">
      <div class="composer-inner">
        <textarea
          ref="composerRef"
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
    </div>
  </section>
</template>

<style scoped>
.chat {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
  overflow: hidden;
}

.chat-surface {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chat-head {
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.85rem 1rem 0.65rem;
  border-bottom: 1px solid var(--color-border);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, var(--color-surface) 100%);
}

.chat-head-text {
  flex: 1;
  min-width: 0;
  max-width: var(--max-readable);
}

.new-chat {
  flex-shrink: 0;
  padding: 0.45rem 0.85rem;
  font-size: 0.8125rem;
  font-weight: 600;
}

.chat-title {
  font-size: 1.1rem;
  margin: 0 0 0.2rem;
}

.hint {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-warm);
}

.banner {
  flex-shrink: 0;
  margin: 0;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  background: rgba(198, 125, 78, 0.12);
  color: #7a4a2a;
  border-bottom: 1px solid rgba(198, 125, 78, 0.15);
}

.scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.scroll-pad {
  padding: 1rem 1rem 1.25rem;
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
  max-width: min(85%, 36rem);
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
  box-shadow: 0 4px 16px rgba(61, 107, 92, 0.25);
}

.row.assistant .bubble {
  background: var(--color-canvas-2);
  color: var(--color-ink);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: var(--radius-sm);
}

.typing {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  min-width: 4rem;
  padding: 0.5rem 0.25rem 0.65rem;
}

.typing--wide {
  align-items: flex-start;
  min-width: min(100%, 18rem);
  max-width: min(85%, 36rem);
}

.typing-dots {
  display: flex;
  gap: 0.35rem;
  align-items: center;
  justify-content: center;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-ink-faint);
  animation: bounce 1.2s ease infinite;
}

.typing-dots .dot:nth-child(2) {
  animation-delay: 0.15s;
}
.typing-dots .dot:nth-child(3) {
  animation-delay: 0.3s;
}

.stream-caption {
  margin: 0;
  width: 100%;
  font-size: 0.8125rem;
  line-height: 1.45;
  font-weight: 500;
  color: var(--color-ink-muted);
  animation: captionIn 0.35s ease;
}

@keyframes captionIn {
  from {
    opacity: 0;
    transform: translateY(3px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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
  flex-shrink: 0;
  border-top: 1px solid var(--color-border-strong);
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(8px);
  box-shadow: 0 -12px 32px rgba(26, 23, 20, 0.07);
  padding: 0.75rem 1rem max(0.75rem, env(safe-area-inset-bottom, 0px));
}

.composer-inner {
  display: flex;
  gap: 0.65rem;
  align-items: flex-end;
  max-width: var(--max-content);
  margin: 0 auto;
}

.composer-input {
  flex: 1;
  resize: none;
  min-height: 2.75rem;
  max-height: 8rem;
}

.send {
  flex-shrink: 0;
}
</style>
