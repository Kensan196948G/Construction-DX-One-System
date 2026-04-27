import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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

export default router
