import { defineStore } from 'pinia'
import { getToken, getUser, setToken, setUser, api } from '../api/client'

export const useAuth = defineStore('auth', {
  state: () => ({
    token: getToken(),
    user: getUser(),
    status: null,                      // 模型链健康状态缓存
    demoMode: localStorage.getItem('acp_demo') === '1'   // 演示数据模式
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => !!s.user?.is_admin
  },
  actions: {
    async login(username, password) {
      const data = await api.login(username, password)
      setToken(data.token); setUser(data.user)
      this.token = data.token; this.user = data.user
    },
    logout() {
      setToken(''); setUser(null)
      this.token = ''; this.user = null
    },
    setDemo(v) {
      this.demoMode = v
      localStorage.setItem('acp_demo', v ? '1' : '0')
    },
    async refreshStatus() {
      try { this.status = await api.systemStatus() } catch { this.status = null }
    }
  }
})
