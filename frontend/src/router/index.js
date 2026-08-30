import { createRouter, createWebHistory } from 'vue-router'
import { getToken, getUser } from '../api/client'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
  { path: '/script', name: 'script', component: () => import('../views/ScriptView.vue') },
  { path: '/titles', name: 'titles', component: () => import('../views/TitlesView.vue') },
  { path: '/copywriting', name: 'copywriting', component: () => import('../views/CopywritingView.vue') },
  { path: '/batch', name: 'batch', component: () => import('../views/BatchView.vue') },
  { path: '/history', name: 'history', component: () => import('../views/HistoryView.vue') },
  { path: '/templates', name: 'templates', component: () => import('../views/TemplatesView.vue') },
  { path: '/admin', name: 'admin', component: () => import('../views/AdminView.vue'), meta: { admin: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to) => {
  if (!to.meta.public && !getToken()) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.meta.admin && !getUser()?.is_admin) return { path: '/' }
  return true
})

export default router
