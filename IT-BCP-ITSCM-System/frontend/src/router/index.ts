import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView, meta: { requiresAuth: true } },
    {
      path: '/incidents',
      name: 'incidents',
      component: () => import('@/views/IncidentsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/systems',
      name: 'systems',
      component: () => import('@/views/SystemsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/exercises',
      name: 'exercises',
      component: () => import('@/views/ExercisesView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next({ name: 'login' })
  } else if (to.name === 'login' && auth.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
