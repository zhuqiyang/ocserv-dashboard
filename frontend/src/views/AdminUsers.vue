<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('admin.title') }}</h2>
      <p>{{ $t('admin.subtitle') }}</p>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="user-count">{{ $t('admin.totalUsers', { n: users.length }) }}</span>
        <span v-if="onlineCount > 0" class="online-count">{{ $t('admin.usersOnline', { n: onlineCount }) }}</span>
      </div>
      <button class="btn btn-primary" @click="showAddModal = true">{{ $t('admin.addUser') }}</button>
    </div>

    <!-- User list -->
    <div class="card" style="padding:0">
      <div class="table-wrapper">
        <table v-if="users.length > 0">
          <thead>
            <tr>
              <th>{{ $t('admin.usernameCol') }}</th>
              <th>{{ $t('admin.groupCol') }}</th>
              <th>{{ $t('admin.statusCol') }}</th>
              <th>{{ $t('admin.actionsCol') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.username">
              <td>
                <strong>{{ u.username }}</strong>
                <span v-if="u.username === currentUser" class="you-tag">{{ $t('admin.me') }}</span>
              </td>
              <td>{{ u.group || '*' }}</td>
              <td>
                <span :class="['status-badge', u.online ? 'status-online' : 'status-offline']">
                  {{ u.online ? $t('admin.online') : $t('admin.offline') }}
                </span>
                <span v-if="u.locked" class="status-badge status-locked" style="margin-left:6px">{{ $t('admin.locked') }}</span>
              </td>
              <td>
                <div class="action-btns">
                  <button
                    v-if="u.username !== 'admin'"
                    class="btn btn-sm btn-warning"
                    @click="toggleLock(u)"
                  >
                    {{ u.locked ? $t('admin.unlock') : $t('admin.lock') }}
                  </button>
                  <button
                    v-if="u.online"
                    class="btn btn-sm btn-outline"
                    @click="disconnectUser(u.username)"
                  >
                    {{ $t('admin.disconnect') }}
                  </button>
                  <button
                    v-if="u.username !== 'admin'"
                    class="btn btn-sm btn-danger"
                    @click="confirmDelete(u)"
                  >
                    {{ $t('admin.delete') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else style="padding:40px;text-align:center;color:#6b7280">
          <p>{{ $t('admin.noUsers') }}</p>
        </div>
      </div>
    </div>

    <!-- Refresh button -->
    <div style="text-align:center;margin-top:16px">
      <button class="btn btn-outline" @click="fetchUsers" :disabled="loading">
        <span v-if="loading" class="spinner"></span>
        <span v-else>{{ $t('admin.refresh') }}</span>
      </button>
    </div>

    <!-- Add user modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal">
        <h3 class="modal-title">{{ $t('admin.addUserTitle') }}</h3>
        <div v-if="formError" class="alert alert-error">{{ formError }}</div>
        <form @submit.prevent="addUser">
          <div class="form-group">
            <label class="form-label">{{ $t('admin.usernameLabel') }}</label>
            <input
              v-model="newUser.username"
              type="text"
              class="form-input"
              :placeholder="$t('admin.usernamePlaceholder')"
              required
              pattern="[a-zA-Z0-9_\-\.@]+"
            />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('admin.passwordLabel') }}</label>
            <input
              v-model="newUser.password"
              type="password"
              class="form-input"
              :placeholder="$t('admin.passwordPlaceholder')"
              required
              minlength="6"
            />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('admin.groupLabel') }}</label>
            <input
              v-model="newUser.group"
              type="text"
              class="form-input"
              :placeholder="$t('admin.groupPlaceholder')"
            />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn btn-outline" @click="showAddModal = false">{{ $t('admin.cancel') }}</button>
            <button type="submit" class="btn btn-primary" :disabled="formLoading">
              <span v-if="formLoading" class="spinner"></span>
              <span v-else>{{ $t('admin.createUser') }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal">
        <h3 class="modal-title">{{ $t('admin.deleteUserTitle') }}</h3>
        <p style="margin-bottom:20px;color:#4b5563">
          {{ $t('admin.deleteConfirm', { username: deleteTarget?.username }) }}
        </p>
        <div class="modal-actions">
          <button class="btn btn-outline" @click="showDeleteModal = false">{{ $t('admin.cancel') }}</button>
          <button class="btn btn-danger" @click="deleteUser" :disabled="formLoading">
            <span v-if="formLoading" class="spinner"></span>
            <span v-else>{{ $t('admin.confirmDelete') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AdminUsersView',
  data() {
    return {
      users: [],
      onlineUsers: [],
      error: '',
      success: '',
      loading: false,
      showAddModal: false,
      showDeleteModal: false,
      deleteTarget: null,
      newUser: { username: '', password: '', group: '*' },
      formError: '',
      formLoading: false,
      currentUser: '',
    }
  },
  computed: {
    onlineCount() {
      return this.users.filter(u => u.online).length
    },
  },
  async mounted() {
    const userStr = localStorage.getItem('ocserv_user')
    if (userStr) {
      try {
        this.currentUser = JSON.parse(userStr).username || ''
      } catch {}
    }
    await this.fetchUsers()
  },
  methods: {
    async fetchUsers() {
      this.loading = true
      this.error = ''
      try {
        const token = localStorage.getItem('ocserv_token')
        const res = await axios.get('/api/users', {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.users = res.data.users
      } catch (err) {
        this.error = err.response?.data?.error || this.$t('admin.fetchError')
      } finally {
        this.loading = false
      }
    },
    async addUser() {
      this.formError = ''
      this.formLoading = true
      try {
        const token = localStorage.getItem('ocserv_token')
        await axios.post('/api/users', this.newUser, {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.showAddModal = false
        this.newUser = { username: '', password: '', group: '*' }
        this.success = this.$t('admin.createSuccess')
        await this.fetchUsers()
        setTimeout(() => { this.success = '' }, 3000)
      } catch (err) {
        this.formError = err.response?.data?.error || this.$t('admin.createFailed')
      } finally {
        this.formLoading = false
      }
    },
    confirmDelete(user) {
      this.deleteTarget = user
      this.showDeleteModal = true
    },
    async deleteUser() {
      if (!this.deleteTarget) return
      this.formLoading = true
      try {
        const token = localStorage.getItem('ocserv_token')
        await axios.delete(`/api/users/${this.deleteTarget.username}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.showDeleteModal = false
        this.deleteTarget = null
        this.success = this.$t('admin.deleteSuccess')
        await this.fetchUsers()
        setTimeout(() => { this.success = '' }, 3000)
      } catch (err) {
        this.formError = err.response?.data?.error || this.$t('admin.deleteFailed')
        this.showDeleteModal = false
      } finally {
        this.formLoading = false
      }
    },
    async toggleLock(user) {
      const action = user.locked ? 'unlock' : 'lock'
      const actionText = user.locked ? this.$t('admin.unlock') : this.$t('admin.lock')
      if (!confirm(this.$t('admin.lockConfirm', { action: actionText, username: user.username }))) return
      try {
        const token = localStorage.getItem('ocserv_token')
        await axios.post(`/api/users/${user.username}/lock`, { action }, {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.success = this.$t('admin.lockSuccess', { action: actionText })
        await this.fetchUsers()
        setTimeout(() => { this.success = '' }, 3000)
      } catch (err) {
        this.error = err.response?.data?.error || this.$t('admin.lockFailed', { action: actionText })
      }
    },
    async disconnectUser(username) {
      if (!confirm(this.$t('admin.disconnectConfirm', { username }))) return
      try {
        const token = localStorage.getItem('ocserv_token')
        await axios.post(`/api/users/${username}/disconnect`, {}, {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.success = this.$t('admin.disconnectSuccess', { username })
        await this.fetchUsers()
        setTimeout(() => { this.success = '' }, 3000)
      } catch (err) {
        this.error = this.$t('admin.disconnectFailed')
      }
    },
  },
}
</script>

<style scoped>
.page {
  max-width: 1000px;
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

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #6b7280;
}

.online-count {
  background: #d1fae5;
  color: #065f46;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.you-tag {
  font-size: 10px;
  font-weight: 700;
  background: #e0e7ff;
  color: #3730a3;
  padding: 1px 6px;
  border-radius: 8px;
  margin-left: 6px;
}

.action-btns {
  display: flex;
  gap: 6px;
}
</style>
