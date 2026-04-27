import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    { path: '/', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true } },
    {
      path: '/rfcs',
      name: 'rfcs',
      component: () => import('@/views/RfcsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/cab',
      name: 'cab',
      component: () => import('@/views/CabView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.name === 'login') return true

  if (to.meta.requiresAuth) {
    const { useAuthStore } = await import('@/stores/auth')
    const auth = useAuthStore()
    if (!auth.isAuthenticated) {
      const ok = await auth.checkAuth()
      if (!ok) return { name: 'login' }
    }
  }

  return true
})

export default router
