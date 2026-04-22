/** Mirrors backend ``UserResponse``. */
export interface User {
  id: string
  name: string
  email: string
  created_at: string
  email_verified: boolean
}

/** Login JSON from ``POST /auth/login``. */
export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

/** Mirrors backend ``ProfileResponse`` / ``ProfileUpdate``. */
export interface Profile {
  id: string
  user_id: string
  summary: string | null
  profession: string | null
  current_salary: number | null
  salary_target: number | null
  technologies: string | null
  programming_languages: string | null
  career_goal: string | null
  location: string | null
  willing_to_relocate: boolean | null
  created_at: string
  updated_at: string
}

export type ProfilePatch = Partial<{
  summary: string | null
  profession: string | null
  current_salary: number | null
  salary_target: number | null
  technologies: string | null
  programming_languages: string | null
  career_goal: string | null
  location: string | null
  willing_to_relocate: boolean | null
}>
