<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('dashboard.title') }}</h2>
      <p>{{ $t('dashboard.welcome', { name: user.username }) }}</p>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <!-- Info cards -->
    <div class="grid-2">
      <div class="card stat-card">
        <div class="stat-icon">👤</div>
        <div class="stat-info">
          <div class="stat-value">{{ user.username }}</div>
          <div class="stat-label">{{ $t('dashboard.username') }}</div>
        </div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon">{{ user.is_admin ? '🛡️' : '🔑' }}</div>
        <div class="stat-info">
          <div class="stat-value">{{ user.is_admin ? $t('dashboard.admin') : $t('dashboard.normalUser') }}</div>
          <div class="stat-label">{{ $t('dashboard.role') }}</div>
        </div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon">{{ user.online ? '🟢' : '⚫' }}</div>
        <div class="stat-info">
          <div class="stat-value">{{ user.online ? $t('dashboard.online') : $t('dashboard.offline') }}</div>
          <div class="stat-label">{{ $t('dashboard.vpnStatus') }}</div>
        </div>
      </div>
      <div class="card stat-card">
        <div class="stat-icon">📂</div>
        <div class="stat-info">
          <div class="stat-value">{{ user.group || '*' }}</div>
          <div class="stat-label">{{ $t('dashboard.group') }}</div>
        </div>
      </div>
    </div>

    <!-- Admin: server status & online users -->
    <template v-if="user.is_admin">
      <div class="card">
        <div class="card-title">{{ $t('dashboard.serverStatus') }}</div>
        <div class="table-wrapper" v-if="serverStatus">
          <table>
            <tbody>
              <tr>
                <td style="width:200px;font-weight:600">{{ $t('dashboard.runStatus') }}</td>
                <td>
                  <span :class="['status-badge', serverStatus.running ? 'status-online' : 'status-offline']">
                    {{ serverStatus.running ? $t('dashboard.running') : $t('dashboard.stopped') }}
                  </span>
                </td>
              </tr>
              <tr v-if="serverStatus.running && serverStatus['Connected Clients'] != null">
                <td style="font-weight:600">{{ $t('dashboard.connectedClients') }}</td>
                <td>{{ serverStatus['Connected Clients'] }}</td>
              </tr>
              <tr v-if="serverStatus.running && serverStatus['Active Sessions'] != null">
                <td style="font-weight:600">{{ $t('dashboard.activeSessions') }}</td>
                <td>{{ serverStatus['Active Sessions'] }}</td>
              </tr>
              <tr v-if="serverStatus.running && serverStatus.Uptime">
                <td style="font-weight:600">{{ $t('dashboard.uptime') }}</td>
                <td>{{ serverStatus.Uptime }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="spinner"></div>
      </div>

      <div class="card">
        <div class="card-title">
          {{ $t('dashboard.onlineUsers') }}
          <span style="font-weight:400;font-size:14px;color:#6b7280;margin-left:8px">
            ({{ $t('dashboard.usersOnline', { n: onlineUsers.length }) }})
          </span>
        </div>
        <div v-if="onlineUsers.length > 0" class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>{{ $t('dashboard.usernameCol') }}</th>
                <th>{{ $t('dashboard.ipAddress') }}</th>
                <th>{{ $t('dashboard.connectTime') }}</th>
                <th>{{ $t('dashboard.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in onlineUsers" :key="u.username">
                <td><strong>{{ u.username }}</strong></td>
                <td>{{ u.ip || '-' }}</td>
                <td>{{ u.since || '-' }}</td>
                <td>
                  <button class="btn btn-sm btn-warning" @click="disconnectUser(u.username)">{{ $t('dashboard.disconnect') }}</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else style="color:#6b7280;font-size:14px">{{ $t('dashboard.noOnlineUsers') }}</p>
      </div>
    </template>

    <!-- Quick actions -->
    <div class="card" style="margin-top:16px">
      <div class="card-title">{{ $t('dashboard.quickActions') }}</div>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <router-link to="/change-password" class="btn btn-outline">{{ $t('dashboard.changePassword') }}</router-link>
        <router-link v-if="user.is_admin" to="/admin/users" class="btn btn-primary">{{ $t('dashboard.manageUsers') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DashboardView',
  data() {
    return {
      user: {
        username: '',
        is_admin: false,
        online: false,
        group: '',
      },
      serverStatus: null,
      onlineUsers: [],
      error: '',
    }
  },
  async mounted() {
    await this.fetchUserInfo()
    if (this.user.is_admin) {
      await Promise.all([this.fetchServerStatus(), this.fetchOnlineUsers()])
    }
  },
  methods: {
    async fetchUserInfo() {
      try {
        const token = localStorage.getItem('ocserv_token')
        const res = await axios.get('/api/me', {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.user = res.data
      } catch (err) {
        this.error = this.$t('dashboard.loadError')
      }
    },
    async fetchServerStatus() {
      try {
        const token = localStorage.getItem('ocserv_token')
        const res = await axios.get('/api/server/status', {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.serverStatus = res.data
      } catch {
        this.serverStatus = { running: false }
      }
    },
    async fetchOnlineUsers() {
      try {
        const token = localStorage.getItem('ocserv_token')
        const res = await axios.get('/api/users/online', {
          headers: { Authorization: `Bearer ${token}` },
        })
        this.onlineUsers = Object.entries(res.data.details || {}).map(([name, info]) => ({
          username: name,
          ip: info['Remote IP'] || info['IP'] || info['ip'] || '-',
          since: info['Connected'] || info['Connected At'] || info['since'] || '-',
        }))
      } catch {
        this.onlineUsers = []
      }
    },
    async disconnectUser(username) {
      if (!confirm(this.$t('dashboard.disconnectConfirm', { username }))) return
      try {
        const token = localStorage.getItem('ocserv_token')
        await axios.post(`/api/users/${username}/disconnect`, {}, {
          headers: { Authorization: `Bearer ${token}` },
        })
        await this.fetchOnlineUsers()
      } catch (err) {
        alert(this.$t('dashboard.disconnectFailed'))
      }
    },
  },
}
</script>

<style scoped>
.page {
  max-width: 900px;
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

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon { font-size: 32px; }

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-top: 2px;
}
</style>
