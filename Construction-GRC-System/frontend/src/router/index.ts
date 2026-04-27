import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    { path: '/', name: 'dashboard', component: DashboardView },
    {
      path: '/risks',
      name: 'risks',
      component: () => import('@/views/RisksView.vue'),
    },
    {
      path: '/compliance',
      name: 'compliance',
      component: () => import('@/views/ComplianceView.vue'),
    },
    {
      path: '/audits',
      name: 'audits',
      component: () => import('@/views/AuditsView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.path === '/login') {
    if (auth.isAuthenticated) return '/'
    return true
  }
  if (!auth.isAuthenticated) return '/login'
  return true
})

export default router
