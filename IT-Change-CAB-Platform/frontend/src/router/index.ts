import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    {
      path: '/rfcs',
      name: 'rfcs',
      component: () => import('@/views/RfcsView.vue'),
    },
    {
      path: '/cab',
      name: 'cab',
      component: () => import('@/views/CabView.vue'),
    },
  ],
})

export default router
