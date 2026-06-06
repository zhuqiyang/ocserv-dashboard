import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import AdminUsers from '../views/AdminUsers.vue'
import ChangePassword from '../views/ChangePassword.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'Login', component: Login, meta: { guest: true } },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { auth: true } },
  { path: '/admin/users', name: 'AdminUsers', component: AdminUsers, meta: { auth: true, admin: true } },
  { path: '/change-password', name: 'ChangePassword', component: ChangePassword, meta: { auth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('ocserv_token')
  const userStr = localStorage.getItem('ocserv_user')

  if (to.meta.auth && !token) {
    return next('/login')
  }

  if (to.meta.admin && userStr) {
    try {
      const user = JSON.parse(userStr)
      if (!user.is_admin) {
        return next('/dashboard')
      }
    } catch {
      return next('/login')
    }
  }

  if (to.meta.guest && token) {
    return next('/dashboard')
  }

  next()
})

export default router
