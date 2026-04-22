import DOMPurify, { type Config } from 'dompurify'
import { marked } from 'marked'

marked.use({
  gfm: true,
  breaks: true,
})

/** Avoid duplicate hooks when Vite hot-reloads the module. */
const HOOK_FLAG = '__careerCopilotMarkdownPurifyHook'

function ensureAnchorHook(): void {
  const g = globalThis as unknown as Record<string, boolean>
  if (g[HOOK_FLAG]) return
  g[HOOK_FLAG] = true
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName !== 'A' || !(node instanceof HTMLAnchorElement)) return
    const href = (node.getAttribute('href') ?? '').trim()
    if (!href || href.startsWith('#')) {
      node.removeAttribute('target')
      node.setAttribute('rel', 'nofollow noopener noreferrer')
      return
    }
    const lower = href.toLowerCase()
    if (lower.startsWith('mailto:') || lower.startsWith('tel:')) {
      node.removeAttribute('target')
      node.setAttribute('rel', 'nofollow noopener noreferrer')
      return
    }
    node.setAttribute('rel', 'noopener noreferrer nofollow')
    node.setAttribute('target', '_blank')
  })
}

const SANITIZE: Config = {
  RETURN_TRUSTED_TYPE: false,
  ALLOWED_TAGS: [
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'p',
    'blockquote',
    'pre',
    'code',
    'span',
    'ul',
    'ol',
    'li',
    'hr',
    'br',
    'strong',
    'em',
    'b',
    'i',
    'table',
    'thead',
    'tbody',
    'tr',
    'th',
    'td',
    'a',
    'del',
    'ins',
    'sub',
    'sup',
  ],
  ALLOWED_ATTR: ['href', 'title', 'target', 'rel'],
  ALLOW_DATA_ATTR: false,
}

/** Markdown → HTML, sanitized for safe use with `v-html`. */
export function renderSafeMarkdown(raw: string): string {
  ensureAnchorHook()
  const s = raw?.trim()
  if (!s) return ''
  const html = marked.parse(s, { async: false }) as string
  return DOMPurify.sanitize(html, SANITIZE)
}
