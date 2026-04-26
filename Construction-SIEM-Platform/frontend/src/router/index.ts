import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    {
      path: '/events',
      name: 'events',
      component: () => import('@/views/EventsView.vue'),
    },
    {
      path: '/alerts',
      name: 'alerts',
      component: () => import('@/views/AlertsView.vue'),
    },
  ],
})

export default router
