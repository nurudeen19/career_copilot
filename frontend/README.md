# Frontend

Vue 3 + Vite single-page application for Career Copilot. Real-time workflow streaming with Pinia state management.

## Quick Start

### Prerequisites

- Node.js 24+ with npm/pnpm
- Backend running on `localhost:8000` (or configure proxy)

### Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start development server
npm run dev
```

**Application available at:**
- **Dev Server:** http://127.0.0.1:5173
- **Hot Module Reload (HMR):** Automatic on file save

---

## Configuration

### API Proxy

Development proxy configured in `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    }
  }
}
```

**Environment-specific:**
- **Development:** `http://127.0.0.1:8000`
- **Production:** Configure via `VITE_API_URL` in `.env`

### Environment Variables

Create `.env.local`:
```bash
VITE_API_URL=http://localhost:8000
VITE_LOG_LEVEL=debug  # or 'info', 'warn', 'error'
```

Build-time variables (define in `.env`, use as `import.meta.env.*`):
```bash
VITE_API_URL=...      # Auto-prefixed with VITE_
VITE_APP_VERSION=0.1.0
```

---

## Project Structure

```
frontend/
├── src/
│   ├── App.vue                 # Root component
│   ├── main.ts                 # Vite entry point
│   ├── env.d.ts               # TypeScript env types
│   │
│   ├── components/
│   │   ├── ChatMessage.vue     # Single message display
│   │   ├── ChatInput.vue       # Message input field
│   │   ├── WorkflowStages.vue  # Stage indicators
│   │   ├── ProfileCard.vue     # User profile display
│   │   └── ... (other components)
│   │
│   ├── views/
│   │   ├── ChatView.vue        # Main chat interface
│   │   ├── ProfileView.vue     # User profile page
│   │   ├── AuthView.vue        # Login/register
│   │   └── DashboardView.vue   # Dashboard
│   │
│   ├── router/
│   │   └── index.ts            # Vue Router setup
│   │
│   ├── stores/                 # Pinia state management
│   │   ├── auth.ts             # Authentication state
│   │   ├── chat.ts             # Chat/workflow state
│   │   ├── profile.ts          # User profile state
│   │   └── ui.ts               # UI state (theme, etc.)
│   │
│   ├── composables/
│   │   ├── useAuth.ts          # Auth composition
│   │   ├── useChat.ts          # Chat logic
│   │   ├── useEventStream.ts   # SSE streaming
│   │   └── ... (other composables)
│   │
│   ├── api/
│   │   ├── client.ts           # Axios client setup
│   │   ├── auth.ts             # Auth API calls
│   │   ├── chat.ts             # Chat/workflow API
│   │   ├── profile.ts          # Profile API
│   │   └── health.ts           # Health check
│   │
│   ├── types/
│   │   ├── auth.ts             # Auth types
│   │   ├── chat.ts             # Chat types
│   │   ├── workflow.ts         # Workflow types
│   │   └── ... (other types)
│   │
│   ├── utils/
│   │   ├── token.ts            # JWT token helpers
│   │   ├── format.ts           # Formatting utilities
│   │   ├── api.ts              # API error handling
│   │   └── ... (other utilities)
│   │
│   ├── assets/
│   │   ├── logo.svg
│   │   └── ... (static assets)
│   │
│   └── styles/
│       ├── global.css          # Global styles
│       ├── variables.css       # CSS variables
│       └── ... (component styles)
│
├── public/                     # Static files (copied to root on build)
│
├── index.html                  # HTML entry point
├── tsconfig.json               # TypeScript config
├── tsconfig.app.json           # App TypeScript config
├── tsconfig.node.json          # Node TypeScript config
├── vite.config.ts              # Vite configuration
├── eslint.config.ts            # ESLint configuration
├── env.d.ts                    # Environment type definitions
├── package.json
└── README.md                   # This file
```

---

## Development

### Scripts

```bash
npm run dev       # Start dev server with HMR
npm run build     # Production build
npm run preview   # Preview production build
npm run lint      # Run ESLint
npm run type-check # Run TypeScript type check
```

### Hot Module Reload (HMR)

Changes to `.vue`, `.ts`, or `.css` files automatically reload in browser without losing state.

### Type Checking

```bash
npm run type-check  # Check TypeScript errors
npm run lint        # Check ESLint + format
```


## References

- [Vue 3 Docs](https://vuejs.org/)
- [Vite Docs](https://vitejs.dev/)
- [Pinia Docs](https://pinia.vuejs.org/)
- [Vue Router Docs](https://router.vuejs.org/)
- [TypeScript Vue Plugin](https://github.com/johnsoncodehk/volar)
- [Architecture Guide](../docs/architecture.md)
- [Backend API](../backend/README.md)
