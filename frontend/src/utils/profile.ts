import type { Profile } from '@/types/models'

/** Minimum fields before we allow career chat (matches product expectation). */
export function isProfileComplete(p: Profile | null): boolean {
  if (!p) return false
  const prof = (p.profession ?? '').trim()
  const goal = (p.career_goal ?? '').trim()
  const anchor = (p.location ?? '').trim() || (p.summary ?? '').trim()
  return Boolean(prof && goal && anchor)
}
