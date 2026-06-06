<template>
  <div id="app-root">
    <nav v-if="isLoggedIn" class="navbar">
      <div class="nav-brand">
        <span class="nav-logo">🔐</span>
        <span class="nav-title">{{ $t('nav.title') }}</span>
      </div>
      <div class="nav-links">
        <router-link to="/dashboard">{{ $t('nav.dashboard') }}</router-link>
        <router-link v-if="isAdmin" to="/admin/users">{{ $t('nav.userManagement') }}</router-link>
        <router-link to="/change-password">{{ $t('nav.changePassword') }}</router-link>
        <a href="#" @click.prevent="logout">{{ $t('nav.logout') }}</a>
      </div>
      <div class="nav-right">
        <div class="lang-switch">
          <button
            :class="['lang-btn', { active: currentLang === 'zh-CN' }]"
            @click="switchLang('zh-CN')"
            title="中文"
          >中</button>
          <button
            :class="['lang-btn', { active: currentLang === 'en' }]"
            @click="switchLang('en')"
            title="English"
          >EN</button>
        </div>
        <div class="nav-user">
          <span class="user-badge">{{ currentUser }}</span>
          <span v-if="isAdmin" class="admin-badge">{{ $t('nav.admin') }}</span>
        </div>
      </div>
    </nav>
    <main :class="{ 'with-nav': isLoggedIn }">
      <router-view @login="onLogin" />
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

export default {
  name: 'App',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const { locale } = useI18n()

    const currentUser = ref('')
    const isAdmin = ref(false)
    const currentLang = ref(locale.value)

    const isLoggedIn = computed(() => !!localStorage.getItem('ocserv_token'))

    function updateUserInfo() {
      const userStr = localStorage.getItem('ocserv_user')
      if (userStr) {
        try {
          const user = JSON.parse(userStr)
          currentUser.value = user.username || ''
          isAdmin.value = user.is_admin || false
        } catch {
          currentUser.value = ''
          isAdmin.value = false
        }
      }
    }

    function switchLang(lang) {
      locale.value = lang
      currentLang.value = lang
      localStorage.setItem('ocserv_lang', lang)
      document.documentElement.lang = lang === 'zh-CN' ? 'zh-CN' : 'en'
    }

    function onLogin(user) {
      localStorage.setItem('ocserv_token', user.token)
      localStorage.setItem('ocserv_user', JSON.stringify({
        username: user.username,
        is_admin: user.is_admin,
      }))
      updateUserInfo()
      router.push('/dashboard')
    }

    function logout() {
      localStorage.removeItem('ocserv_token')
      localStorage.removeItem('ocserv_user')
      currentUser.value = ''
      isAdmin.value = false
      router.push('/login')
    }

    onMounted(() => {
      updateUserInfo()
      document.documentElement.lang = locale.value === 'zh-CN' ? 'zh-CN' : 'en'
    })

    return { currentUser, isAdmin, isLoggedIn, currentLang, onLogin, logout, switchLang }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f0f2f5;
  color: #1a1a2e;
  min-height: 100vh;
}

/* Navbar */
.navbar {
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-right: 32px;
}

.nav-logo { font-size: 24px; }
.nav-title { font-size: 18px; font-weight: 700; letter-spacing: -0.5px; }

.nav-links {
  display: flex;
  gap: 8px;
  flex: 1;
}

.nav-links a {
  color: #a8b2d1;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #fff;
  background: rgba(255,255,255,0.1);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.lang-switch {
  display: flex;
  gap: 2px;
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 2px;
}

.lang-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  background: transparent;
  color: #a8b2d1;
  transition: all 0.2s;
}

.lang-btn.active {
  background: rgba(255,255,255,0.2);
  color: #fff;
}

.lang-btn:hover:not(.active) {
  color: #ccd6f6;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-badge {
  font-size: 14px;
  font-weight: 500;
  color: #ccd6f6;
}

.admin-badge {
  font-size: 11px;
  font-weight: 700;
  background: #e94560;
  color: #fff;
  padding: 2px 8px;
  border-radius: 12px;
}

main {
  min-height: 100vh;
}

main.with-nav {
  padding-top: 56px;
}

/* Reusable card style */
.card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  padding: 24px;
  margin-bottom: 16px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1a1a2e;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
}

.btn-primary {
  background: linear-gradient(135deg, #0f3460, #16213e);
  color: #fff;
}
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(15,52,96,0.3); }

.btn-danger {
  background: linear-gradient(135deg, #e94560, #c23152);
  color: #fff;
}
.btn-danger:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(233,69,96,0.3); }

.btn-success {
  background: linear-gradient(135deg, #0f9b58, #0a7a43);
  color: #fff;
}

.btn-warning {
  background: linear-gradient(135deg, #f0a500, #d18e00);
  color: #fff;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
}

.btn-outline {
  background: transparent;
  border: 2px solid #d1d5db;
  color: #4b5563;
}
.btn-outline:hover { border-color: #0f3460; color: #0f3460; }

/* Form elements */
.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #4b5563;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 15px;
  transition: border-color 0.2s;
  outline: none;
  background: #f9fafb;
}

.form-input:focus {
  border-color: #0f3460;
  background: #fff;
}

.form-select {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 15px;
  background: #f9fafb;
  outline: none;
}

/* Alert messages */
.alert {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 16px;
  font-weight: 500;
}

.alert-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.alert-success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.alert-info {
  background: #eff6ff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}

/* Grid */
.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

/* Table */
.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 700;
  color: #6b7280;
  border-bottom: 2px solid #e5e7eb;
  background: #f9fafb;
}

td {
  padding: 12px 16px;
  font-size: 14px;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: middle;
}

tr:hover td {
  background: #f9fafb;
}

/* Status badges */
.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-online {
  background: #d1fae5;
  color: #065f46;
}

.status-offline {
  background: #f3f4f6;
  color: #6b7280;
}

.status-locked {
  background: #fef2f2;
  color: #991b1b;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  backdrop-filter: blur(4px);
}

.modal {
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  width: 90%;
  max-width: 480px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}

.modal-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 24px;
}

/* Loading spinner */
.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #0f3460;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Transition */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
