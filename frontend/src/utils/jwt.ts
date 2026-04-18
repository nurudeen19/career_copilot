/** Decode JWT payload (no signature verification — display / correlation only). */
export function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const part = token.split('.')[1]
    if (!part) return null
    const b64 = part.replace(/-/g, '+').replace(/_/g, '/')
    const json = JSON.parse(atob(b64))
    return typeof json === 'object' && json !== null ? json : null
  } catch {
    return null
  }
}

export function decodeJwtSub(token: string): string | null {
  const p = decodeJwtPayload(token)
  const sub = p?.sub
  return typeof sub === 'string' ? sub : null
}
