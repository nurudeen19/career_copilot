const STORAGE_KEY = 'career_copilot_token'

export function apiBase(): string {
  const env = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '')
  if (env) return env
  if (import.meta.env.DEV) return '/api'
  return ''
}

export function getStoredToken(): string | null {
  return localStorage.getItem(STORAGE_KEY)
}

export function setStoredToken(token: string | null): void {
  if (token) localStorage.setItem(STORAGE_KEY, token)
  else localStorage.removeItem(STORAGE_KEY)
}

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

function formatFastApiDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (!Array.isArray(detail)) return typeof detail === 'object' && detail !== null ? JSON.stringify(detail) : String(detail)
  const parts: string[] = []
  for (const item of detail) {
    if (item && typeof item === 'object' && 'msg' in item) {
      let m = String((item as { msg: string }).msg)
      if (m.startsWith('Value error, ')) m = m.slice('Value error, '.length)
      parts.push(m)
    }
  }
  return parts.length > 0 ? parts.join(' ') : JSON.stringify(detail)
}

async function parseDetail(res: Response): Promise<string> {
  try {
    const j = (await res.json()) as { detail?: unknown }
    if (typeof j.detail === 'string') return j.detail
    if (j.detail !== undefined) return formatFastApiDetail(j.detail)
  } catch {
    /* ignore */
  }
  return res.statusText || 'Request failed'
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { skipAuth?: boolean } = {},
): Promise<T> {
  const url = `${apiBase()}${path.startsWith('/') ? path : `/${path}`}`
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (!init.skipAuth) {
    const t = getStoredToken()
    if (t) headers.set('Authorization', `Bearer ${t}`)
  }
  let res: Response
  try {
    res = await fetch(url, { ...init, headers })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    if (e instanceof TypeError || msg === 'Failed to fetch' || msg.includes('fetch')) {
      throw new ApiError(
        0,
        'Could not reach the API (network error). If you are running locally, start the backend and check the dev proxy / VITE_API_BASE_URL.',
      )
    }
    throw e
  }
  if (!res.ok) throw new ApiError(res.status, await parseDetail(res))
  if (res.status === 204) return undefined as T
  const ct = res.headers.get('content-type')
  if (ct?.includes('application/json')) return (await res.json()) as T
  return (await res.text()) as T
}
