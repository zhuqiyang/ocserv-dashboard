<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('password.title') }}</h2>
      <p>{{ $t('password.subtitle') }}</p>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <div class="card" style="max-width:480px">
      <form @submit.prevent="changePassword">
        <div class="form-group">
          <label class="form-label">{{ $t('password.currentPassword') }}</label>
          <input
            v-model="currentPassword"
            type="password"
            class="form-input"
            :placeholder="$t('password.currentPlaceholder')"
            autocomplete="current-password"
            required
          />
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('password.newPassword') }}</label>
          <input
            v-model="newPassword"
            type="password"
            class="form-input"
            :placeholder="$t('password.newPlaceholder')"
            autocomplete="new-password"
            required
            minlength="6"
          />
        </div>
        <div class="form-group">
          <label class="form-label">{{ $t('password.confirmPassword') }}</label>
          <input
            v-model="confirmPassword"
            type="password"
            class="form-input"
            :placeholder="$t('password.confirmPlaceholder')"
            autocomplete="new-password"
            required
          />
        </div>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>{{ $t('password.submit') }}</span>
        </button>
      </form>
    </div>

    <div class="card" style="max-width:480px;margin-top:16px">
      <div class="card-title">{{ $t('password.requirements') }}</div>
      <ul style="padding-left:20px;font-size:14px;color:#4b5563;line-height:2">
        <li>{{ $t('password.req1') }}</li>
        <li>{{ $t('password.req2') }}</li>
        <li>{{ $t('password.req3') }}</li>
      </ul>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ChangePasswordView',
  data() {
    return {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
      error: '',
      success: '',
      loading: false,
    }
  },
  methods: {
    async changePassword() {
      this.error = ''
      this.success = ''

      if (this.newPassword.length < 6) {
        this.error = this.$t('password.tooShort')
        return
      }

      if (this.newPassword !== this.confirmPassword) {
        this.error = this.$t('password.mismatch')
        return
      }

      if (this.currentPassword === this.newPassword) {
        this.error = this.$t('password.sameAsCurrent')
        return
      }

      this.loading = true
      try {
        const token = localStorage.getItem('ocserv_token')
        const res = await axios.post('/api/change-password', {
          current_password: this.currentPassword,
          new_password: this.newPassword,
        }, {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.success = res.data.message || this.$t('password.success')
        this.currentPassword = ''
        this.newPassword = ''
        this.confirmPassword = ''
      } catch (err) {
        this.error = err.response?.data?.error || this.$t('password.failed')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.page {
  max-width: 600px;
  margin: 0 auto;
  padding: 32px 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
}

.page-header p {
  font-size: 15px;
  color: #6b7280;
  margin-top: 4px;
}
</style>
