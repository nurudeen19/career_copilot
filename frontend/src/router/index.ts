import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
      meta: { guestLayout: true },
    },
    {
      path: '/signin',
      name: 'signin',
      component: () => import('@/views/SignInView.vue'),
      meta: { guestLayout: true },
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('@/views/SignUpView.vue'),
      meta: { guestLayout: true },
    },
    {
      path: '/verify-email',
      name: 'verify-email',
      component: () => import('@/views/VerifyEmailView.vue'),
      meta: { guestLayout: true },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (auth.token && (auth.user === null || auth.user.email_verified !== true)) {
    await auth.hydrateUserIfNeeded()
  }

  if (to.meta.requiresAuth && !auth.canUseApp) {
    return { name: 'signin', query: { next: to.fullPath } }
  }

  if ((to.name === 'signin' || to.name === 'signup' || to.name === 'verify-email') && auth.canUseApp) {
    return { name: 'dashboard' }
  }
  return true
})

export default router
