<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'

import {
  streamWorkflow,
  extractAssistantTextFromPatch,
  extractValidationError,
} from '@/composables/useWorkflowStream'
import { ApiError, deleteWorkflowThread } from '@/api/client'
import { renderSafeMarkdown } from '@/utils/safeMarkdown'

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  /** True when this reply came from a run that executed research → … → synthesizer. */
  researchBacked?: boolean
  /** Local only: thumbs already chosen (up = no server call; down triggered replan stream). */
  userRating?: 'up' | 'down'
}

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
/** Assistant message we tried to send thumbs-down feedback for; allows one-click retry after failure. */
const thumbDownRetryFor = ref<ChatMessage | null>(null)

/** In-progress reply text while SSE steps arrive (cleared when the turn finishes). */
const liveStreamDraft = ref('')
let liveDraftScrollTimer: ReturnType<typeof setTimeout> | null = null

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
  user_handoff: 'Finishing up…',
}

/** Steps that mean the user saw a researched pipeline answer (eligible for thumbs). */
const RESEARCH_PIPELINE_STEPS = new Set(['research', 'analyst', 'critic', 'synthesizer'])

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
  liveStreamDraft.value = ''
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

function _patchStr(patch: unknown, path: (string | number)[]): string | null {
  let cur: unknown = patch
  for (const key of path) {
    if (cur === null || cur === undefined) return null
    if (typeof cur !== 'object') return null
    cur = (cur as Record<string, unknown>)[String(key)]
  }
  return typeof cur === 'string' && cur.trim() ? cur.trim() : null
}

function foldAssistantDraftFromStep(step: string, patch: unknown, acc: { text: string }) {
  if (step === 'input_validation') {
    const v = extractValidationError(patch)
    if (v) acc.text = v
  } else if (step === 'validation_fail') {
    const t = extractAssistantTextFromPatch(patch)
    if (t) acc.text = t
  } else if (step === 'user_handoff') {
    const h = extractAssistantTextFromPatch(patch)
    if (h) acc.text = h
  } else if (step === 'planner') {
    const am = _patchStr(patch, ['plan', 'assistant_message'])
    if (am) acc.text = am
  } else if (step === 'research') {
    const rep = _patchStr(patch, ['research', 'research_report'])
    if (rep) acc.text = rep
  } else if (step === 'analyst') {
    const ar = _patchStr(patch, ['analysis', 'analysis_report'])
    if (ar) acc.text = ar
  } else if (step === 'critic') {
    const cr = _patchStr(patch, ['critique', 'critique_report'])
    if (cr) acc.text = cr
  } else if (step === 'synthesizer') {
    const t = extractAssistantTextFromPatch(patch)
    if (t) {
      acc.text = t
      return
    }
    const rec = _patchStr(patch, ['synthesis', 'recommendation'])
    if (rec) acc.text = rec
  }
}

/** Must match ``app.graph.feedback_markers.THUMBS_DOWN_FEEDBACK_MARK`` (opaque; planner asks what's wrong). */
const THUMBS_DOWN_FEEDBACK_MARK = 'USER_THUMBS_DOWN_LAST_PIPELINE_REPLY'

function thumbsDownPlannerFeedback(): string {
  return THUMBS_DOWN_FEEDBACK_MARK
}

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
        const researchBacked = r.researchBacked === true
        const ur = r.userRating
        const userRating = ur === 'up' || ur === 'down' ? ur : undefined
        restored.push({
          id,
          role,
          content: content.trim(),
          ...(researchBacked ? { researchBacked: true } : {}),
          ...(userRating ? { userRating } : {}),
        })
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

async function clearConversation() {
  if (streaming.value) return
  thumbDownRetryFor.value = null
  const tid = threadId.value
  if (tid) {
    try {
      await deleteWorkflowThread(tid)
    } catch (e) {
      error.value =
        e instanceof ApiError ? e.detail : 'Could not clear this conversation on the server. Try again.'
      return
    }
  }
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
        messages: messages.value.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          ...(m.researchBacked ? { researchBacked: true } : {}),
          ...(m.userRating ? { userRating: m.userRating } : {}),
        })),
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

function scheduleScrollForLiveDraft() {
  if (liveDraftScrollTimer !== null) clearTimeout(liveDraftScrollTimer)
  liveDraftScrollTimer = setTimeout(() => {
    liveDraftScrollTimer = null
    void scrollToLatest()
  }, 120)
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
  if (liveDraftScrollTimer !== null) {
    clearTimeout(liveDraftScrollTimer)
    liveDraftScrollTimer = null
  }
})

loadPersistedState()
void scrollToLatest()

type WorkflowTurnResult =
  | { ok: true; assistantText: string; researchBacked: boolean }
  | { ok: false; error: string }

async function runWorkflowTurn(params: {
  message: string
  user_feedback?: string | null
  /** Called after each graph step so the UI can show in-progress text (SSE is incremental). */
  onDraftUpdate?: (text: string) => void
}): Promise<WorkflowTurnResult> {
  const draft = { text: '' }
  let sawChunk = false
  let researchBacked = false

  try {
    for await (const ev of streamWorkflow({
      message: params.message,
      thread_id: threadId.value,
      user_feedback: params.user_feedback ?? null,
    })) {
      if (ev.kind === 'step') {
        sawChunk = true
        onStreamGraphStep(ev.step)
        if (RESEARCH_PIPELINE_STEPS.has(ev.step)) researchBacked = true
        foldAssistantDraftFromStep(ev.step, ev.patch, draft)
        params.onDraftUpdate?.(draft.text)
      } else if (ev.kind === 'done') {
        if (ev.thread_id) {
          threadId.value = ev.thread_id
          sessionStorage.setItem(THREAD_KEY, ev.thread_id)
        }
        const trimmed = draft.text.trim()
        const assistantText =
          trimmed ||
          (sawChunk
            ? 'Here’s what I have so far — feel free to ask for more detail on any part.'
            : '')
        return { ok: true, assistantText, researchBacked }
      } else if (ev.kind === 'error') {
        return { ok: false, error: ev.detail }
      }
    }
    return { ok: false, error: 'Stream ended unexpectedly.' }
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Request failed'
    return { ok: false, error: msg }
  }
}

function onThumbUp(m: ChatMessage) {
  if (streaming.value || m.role !== 'assistant' || m.userRating) return
  m.userRating = 'up'
}

async function onThumbDown(m: ChatMessage) {
  if (streaming.value || m.role !== 'assistant' || m.userRating) return
  if (!props.profileComplete) {
    emit('need-profile')
    return
  }
  if (!threadId.value) {
    error.value = 'Start a conversation first so we can follow up on this thread.'
    return
  }

  thumbDownRetryFor.value = null
  m.userRating = 'down'
  error.value = null
  streaming.value = true
  beginStreamWaitUi()
  await scrollToLatest()

  const result = await runWorkflowTurn({
    message: '',
    user_feedback: thumbsDownPlannerFeedback(),
    onDraftUpdate: (t) => {
      liveStreamDraft.value = t
      scheduleScrollForLiveDraft()
    },
  })

  clearStreamWaitTimers()
  resetStreamUi()
  streaming.value = false
  liveStreamDraft.value = ''

  if (result.ok) {
    thumbDownRetryFor.value = null
    if (result.assistantText.trim()) {
      messages.value.push({
        id: newMessageId(),
        role: 'assistant',
        content: result.assistantText.trim(),
        ...(result.researchBacked ? { researchBacked: true } : {}),
      })
    }
    await scrollToLatest()
    focusComposer()
    return
  }

  error.value = result.error
  thumbDownRetryFor.value = m
  delete m.userRating
  messages.value.push({
    id: newMessageId(),
    role: 'assistant',
    content: `Couldn’t send that feedback — ${result.error}`,
  })
  await scrollToLatest()
  focusComposer()
}

async function retryThumbDownFeedback() {
  const m = thumbDownRetryFor.value
  if (!m || streaming.value) return
  await onThumbDown(m)
}

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

  const result = await runWorkflowTurn({
    message: text,
    onDraftUpdate: (t) => {
      liveStreamDraft.value = t
      scheduleScrollForLiveDraft()
    },
  })

  clearStreamWaitTimers()
  resetStreamUi()
  streaming.value = false
  liveStreamDraft.value = ''

  if (result.ok) {
    if (result.assistantText.trim()) {
      messages.value.push({
        id: newMessageId(),
        role: 'assistant',
        content: result.assistantText.trim(),
        ...(result.researchBacked ? { researchBacked: true } : {}),
      })
    }
    await scrollToLatest()
    focusComposer()
    return
  }

  error.value = result.error
  messages.value.push({
    id: newMessageId(),
    role: 'assistant',
    content: `Something went wrong: ${result.error}`,
  })
  await scrollToLatest()
  focusComposer()
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
          title="Remove this conversation from the server and clear the chat"
          @click="void clearConversation()"
        >
          New chat
        </button>
      </header>

      <p v-if="error" class="banner" role="status">{{ error }}</p>
      <p v-if="thumbDownRetryFor && !streaming" class="retry-feedback" role="status">
        <button type="button" class="cc-btn cc-btn--ghost retry-feedback-btn" @click="void retryThumbDownFeedback()">
          Retry sending feedback
        </button>
      </p>

      <div ref="scrollRef" class="scroll">
        <div class="scroll-pad">
          <div v-for="m in messages" :key="m.id" class="row" :class="m.role">
            <template v-if="m.role === 'user'">
              <!-- eslint-disable-next-line vue/no-v-html -- output from renderSafeMarkdown (marked + DOMPurify) -->
              <div class="bubble md-content md-content--user" v-html="renderSafeMarkdown(m.content)" />
            </template>
            <template v-else>
              <div class="assistant-block">
                <!-- eslint-disable-next-line vue/no-v-html -->
                <div class="bubble md-content" v-html="renderSafeMarkdown(m.content)" />
                <div
                  v-if="m.researchBacked && !m.userRating"
                  class="rating-row"
                  role="group"
                  aria-label="Was this researched summary helpful?"
                >
                  <button
                    type="button"
                    class="rating-btn"
                    :disabled="streaming"
                    aria-label="Thumbs up — helpful"
                    title="Helpful"
                    @click="onThumbUp(m)"
                  >
                    <span class="rating-ico" aria-hidden="true">👍</span>
                  </button>
                  <button
                    type="button"
                    class="rating-btn"
                    :disabled="streaming"
                    aria-label="Thumbs down — ask for a better follow-up"
                    title="Not helpful"
                    @click="onThumbDown(m)"
                  >
                    <span class="rating-ico" aria-hidden="true">👎</span>
                  </button>
                </div>
                <p v-else-if="m.userRating === 'up'" class="rating-note" aria-live="polite">Thanks — glad it helped.</p>
              </div>
            </template>
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
              <div
                v-if="liveStreamDraft.trim()"
                class="stream-live-md md-content"
                aria-live="polite"
                aria-label="Response in progress"
              >
                <!-- eslint-disable-next-line vue/no-v-html -- same pipeline as assistant bubbles -->
                <div v-html="renderSafeMarkdown(liveStreamDraft)" />
              </div>
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

.retry-feedback {
  flex-shrink: 0;
  margin: 0;
  padding: 0.35rem 1rem 0.5rem;
  border-bottom: 1px solid var(--color-border);
}

.retry-feedback-btn {
  font-size: 0.8125rem;
}

.scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
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

.assistant-block {
  max-width: min(85%, 36rem);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0 0.1rem;
}

.rating-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.25rem;
  min-height: 2.25rem;
  padding: 0.2rem 0.45rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.55);
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.rating-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.95);
  border-color: rgba(198, 125, 78, 0.45);
}

.rating-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.rating-note {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--color-muted, #6b6b6b);
}

.bubble {
  max-width: min(85%, 36rem);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-lg);
  font-size: 0.9375rem;
  line-height: 1.55;
}

.md-content {
  white-space: normal;
  overflow-wrap: anywhere;
}

.md-content :deep(p) {
  margin: 0 0 0.65em;
}

.md-content :deep(p:last-child) {
  margin-bottom: 0;
}

.md-content :deep(h1),
.md-content :deep(h2),
.md-content :deep(h3),
.md-content :deep(h4) {
  margin: 0.85em 0 0.4em;
  line-height: 1.25;
  font-weight: 700;
}

.md-content :deep(h1) {
  font-size: 1.2em;
}
.md-content :deep(h2) {
  font-size: 1.1em;
}
.md-content :deep(h3),
.md-content :deep(h4) {
  font-size: 1.02em;
}

.md-content :deep(ul),
.md-content :deep(ol) {
  margin: 0 0 0.65em;
  padding-left: 1.35em;
}

.md-content :deep(li) {
  margin: 0.2em 0;
}

.md-content :deep(blockquote) {
  margin: 0.5em 0;
  padding: 0.35em 0 0.35em 0.85em;
  border-left: 3px solid var(--color-border-strong);
  color: var(--color-ink-muted);
}

.md-content :deep(hr) {
  margin: 0.75em 0;
  border: none;
  border-top: 1px solid var(--color-border);
}

.md-content :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 0.88em;
  padding: 0.12em 0.35em;
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.06);
}

.md-content :deep(pre) {
  margin: 0.5em 0;
  padding: 0.65em 0.85em;
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.06);
  border: 1px solid var(--color-border);
  overflow-x: auto;
}

.md-content :deep(pre code) {
  padding: 0;
  background: none;
  font-size: 0.84em;
  white-space: pre;
}

.md-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.5em 0;
  font-size: 0.9em;
}

.md-content :deep(th),
.md-content :deep(td) {
  border: 1px solid var(--color-border);
  padding: 0.35em 0.5em;
  text-align: left;
}

.md-content :deep(th) {
  background: rgba(0, 0, 0, 0.04);
}

.md-content :deep(a) {
  color: var(--color-accent);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.md-content--user :deep(a) {
  color: #fff;
  text-decoration-color: rgba(255, 255, 255, 0.65);
}

.md-content--user :deep(code),
.md-content--user :deep(pre) {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.25);
}

.md-content--user :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.45);
  color: rgba(255, 255, 255, 0.88);
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

.stream-live-md {
  width: 100%;
  margin-top: 0.25rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--color-border);
  max-height: min(45vh, 28rem);
  overflow-y: auto;
  text-align: left;
  font-size: 0.9rem;
  line-height: 1.45;
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
