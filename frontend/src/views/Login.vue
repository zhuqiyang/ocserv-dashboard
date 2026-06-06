<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">🔐</div>
        <h1>{{ $t('login.title') }}</h1>
        <p>{{ $t('login.subtitle') }}</p>
      </div>

      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <form @submit.prevent="doLogin">
        <div class="form-group">
          <label class="form-label">{{ $t('login.username') }}</label>
          <input
            v-model="username"
            type="text"
            class="form-input"
            :placeholder="$t('login.usernamePlaceholder')"
            autocomplete="username"
            required
            autofocus
          />
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('login.password') }}</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            :placeholder="$t('login.passwordPlaceholder')"
            autocomplete="current-password"
            required
          />
        </div>
        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>{{ $t('login.submit') }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'LoginView',
  emits: ['login'],
  data() {
    return {
      username: '',
      password: '',
      error: '',
      loading: false,
    }
  },
  methods: {
    async doLogin() {
      this.error = ''
      if (!this.username || !this.password) {
        this.error = this.$t('login.emptyFields')
        return
      }

      this.loading = true
      try {
        const res = await axios.post('/api/login', {
          username: this.username,
          password: this.password,
        })
        this.$emit('login', res.data)
      } catch (err) {
        if (err.response && err.response.data) {
          this.error = err.response.data.error || this.$t('login.failed')
        } else {
          this.error = this.$t('login.serverError')
        }
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding: 20px;
}

.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 25px 80px rgba(0,0,0,0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-icon { font-size: 48px; margin-bottom: 12px; }

.login-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 6px;
}

.login-header p {
  font-size: 14px;
  color: #6b7280;
}

.login-btn {
  width: 100%;
  justify-content: center;
  padding: 12px;
  font-size: 16px;
  margin-top: 8px;
}
</style>
