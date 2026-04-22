import { apiBase, getStoredToken } from '@/api/client'

export type StreamEvent =
  | { kind: 'step'; thread_id: string; step: string; patch: unknown }
  | { kind: 'done'; thread_id: string }
  | { kind: 'error'; thread_id: string; detail: string }

function parseSseData(line: string): unknown | null {
  const t = line.trim()
  if (!t.startsWith('data:')) return null
  const raw = t.slice(5).trim()
  if (!raw) return null
  try {
    return JSON.parse(raw) as unknown
  } catch {
    return null
  }
}

export async function* streamWorkflow(params: {
  message: string
  thread_id?: string | null
  user_feedback?: string | null
}): AsyncGenerator<StreamEvent, void, unknown> {
  const base = apiBase()
  const url = `${base}/workflow/stream`
  const token = getStoredToken()
  if (!token) throw new Error('Not signed in')

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message: params.message,
      thread_id: params.thread_id ?? null,
      user_feedback: params.user_feedback ?? null,
    }),
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const j = (await res.json()) as { detail?: string }
      if (j.detail) detail = j.detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }

  const reader = res.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      const data = parseSseData(line)
      if (!data || typeof data !== 'object') continue
      const o = data as Record<string, unknown>
      if (o.event === 'done' && typeof o.thread_id === 'string') {
        yield { kind: 'done', thread_id: o.thread_id }
        continue
      }
      if (o.event === 'error') {
        yield {
          kind: 'error',
          thread_id: typeof o.thread_id === 'string' ? o.thread_id : '',
          detail: typeof o.detail === 'string' ? o.detail : 'Unknown error',
        }
        continue
      }
      if (typeof o.step === 'string' && 'patch' in o && typeof o.thread_id === 'string') {
        yield { kind: 'step', thread_id: o.thread_id, step: o.step, patch: o.patch }
      }
    }
  }
}

/** Best-effort assistant text from a graph ``patch`` (LangChain message_to_dict shape). */
export function extractAssistantTextFromPatch(patch: unknown): string | null {
  if (!patch || typeof patch !== 'object') return null
  const p = patch as Record<string, unknown>
  const msgs = p.messages
  if (!Array.isArray(msgs) || msgs.length === 0) return null
  const last = msgs[msgs.length - 1]
  if (!last || typeof last !== 'object') return null
  const o = last as Record<string, unknown>
  const data = o.data
  if (!data || typeof data !== 'object') return null
  const content = (data as Record<string, unknown>).content
  if (typeof content === 'string' && content.trim()) return content
  if (Array.isArray(content)) {
    const parts = content
      .map((block) => {
        if (typeof block === 'string') return block
        if (block && typeof block === 'object' && 'text' in block) {
          const t = (block as { text?: unknown }).text
          return typeof t === 'string' ? t : ''
        }
        return ''
      })
      .filter(Boolean)
    const joined = parts.join('')
    return joined.trim() ? joined : null
  }
  return null
}

export function extractValidationError(patch: unknown): string | null {
  if (!patch || typeof patch !== 'object') return null
  const ve = (patch as Record<string, unknown>).validation_error
  return typeof ve === 'string' && ve.trim() ? ve : null
}
