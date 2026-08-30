/* 统一 API 客户端：fetch 封装，零冗余依赖。
   统一处理：Token 注入、{code,message,data} 解包、401 跳登录、错误 toast。 */
import { toast } from '../stores/toast'

const BASE = '/api/v1'
const TOKEN_KEY = 'acp_token'

export function getToken() { return localStorage.getItem(TOKEN_KEY) || '' }
export function setToken(t) { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY) }
export function getUser() {
  try { return JSON.parse(localStorage.getItem('acp_user') || 'null') } catch { return null }
}
export function setUser(u) {
  u ? localStorage.setItem('acp_user', JSON.stringify(u)) : localStorage.removeItem('acp_user')
}

async function request(path, { method = 'GET', body, form } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  let payload
  if (form) {
    payload = form
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  let resp
  try {
    resp = await fetch(BASE + path, { method, headers, body: payload })
  } catch {
    toast.error('网络异常，请确认后端服务已启动')
    throw new Error('network')
  }
  let data = null
  try { data = await resp.json() } catch { /* 非 JSON 响应 */ }
  if (resp.status === 401) {
    setToken('')
    toast.error('登录已过期，请重新登录')
    if (!location.pathname.startsWith('/login')) location.href = '/login'
    throw new Error(data?.message || 'unauthorized')
  }
  if (!resp.ok || !data || data.code !== 0) {
    const msg = data?.message || `请求失败（${resp.status}）`
    toast.error(msg)
    throw new Error(msg)
  }
  return data.data
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  del: (path) => request(path, { method: 'DELETE' }),
  upload: (path, form) => request(path, { method: 'POST', form }),
  // ---------- 业务接口 ----------
  login: (username, password) => request('/auth/login', { method: 'POST', body: { username, password } }),
  changePassword: (p) => request('/auth/change-password', { method: 'POST', body: p }),
  systemStatus: () => request('/system/status'),
  systemConfig: () => request('/system/config'),
  updateSystemConfig: (payload) => request('/system/config', { method: 'POST', body: payload }),
  generateScript: (p) => request('/script/generate', { method: 'POST', body: p }),
  generateTitles: (p) => request('/titles/generate', { method: 'POST', body: p }),
  transformCopy: (p) => request('/copywriting/transform', { method: 'POST', body: p }),
  optimizeTts: (text) => request('/tts/optimize', { method: 'POST', body: { text } }),
  createBatch: (p) => request('/batch/tasks', { method: 'POST', body: p }),
  uploadBatch: (form) => request('/batch/tasks/upload', { method: 'POST', form }),
  listBatch: (params = '') => request(`/batch/tasks${params}`),
  batchDetail: (id) => request(`/batch/tasks/${id}`),
  cancelBatch: (id) => request(`/batch/tasks/${id}/cancel`, { method: 'POST' }),
  retryBatch: (id) => request(`/batch/tasks/${id}/retry`, { method: 'POST' }),
  // 标准分页入参：page/page_size/filter_keyword/grade → {total, records}
  listHistory: (params = '') => request(`/history${params}`),
  historyDetail: (id) => request(`/history/${id}`),
  updateHistory: (id, patch) => request(`/history/${id}`, { method: 'PUT', body: patch }),
  deleteHistory: (id) => request(`/history/${id}`, { method: 'DELETE' }),
  purgeHistory: (id) => request(`/history/${id}/hard`, { method: 'DELETE' }),
  restoreHistory: (id) => request(`/history/${id}/restore`, { method: 'POST' }),
  bulkDeleteHistory: (ids) => request('/history/bulk-delete', { method: 'POST', body: { ids } }),
  bulkPurgeHistory: (ids) => request('/history/bulk-purge', { method: 'POST', body: { ids } }),
  listTemplates: (params = '') => request(`/templates${params}`),
  createTemplate: (p) => request('/templates', { method: 'POST', body: p }),
  updateTemplate: (id, p) => request(`/templates/${id}`, { method: 'PUT', body: p }),
  deleteTemplate: (id) => request(`/templates/${id}`, { method: 'DELETE' }),
  // ---------- 管理后台 ----------
  adminUsers: (params = '') => request(`/admin/users${params}`),
  adminCreateUser: (p) => request('/admin/users', { method: 'POST', body: p }),
  adminResetPassword: (id, password) => request(`/admin/users/${id}/reset-password`, { method: 'POST', body: { password } }),
  adminDeleteUser: (id) => request(`/admin/users/${id}`, { method: 'DELETE' }),
  adminLogs: (params = '') => request(`/admin/logs${params}`)
}

export function downloadUrl(path) {
  return `${BASE}${path}${path.includes('?') ? '&' : '?'}_t=${Date.now()}`
}

/** 带鉴权头的文件下载（GET）。返回 blob。 */
export async function downloadFile(path, { onProgress } = {}) {
  if (onProgress) onProgress(true)
  const resp = await fetch(BASE + path, { headers: { Authorization: `Bearer ${getToken()}` } })
  if (!resp.ok) {
    let msg = `下载失败（${resp.status}）`
    try { msg = (await resp.json()).message || msg } catch { /* ignore */ }
    toast.error(msg)
    if (onProgress) onProgress(false)
    throw new Error(msg)
  }
  const blob = await resp.blob()
  if (onProgress) onProgress(false)
  return blob
}
