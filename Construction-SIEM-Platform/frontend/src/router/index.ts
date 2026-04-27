import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true } },
    {
      path: '/events',
      name: 'events',
      component: () => import('@/views/EventsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/alerts',
      name: 'alerts',
      component: () => import('@/views/AlertsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/rules',
      name: 'rules',
      component: () => import('@/views/RulesView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  auth.checkAuth()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && auth.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
