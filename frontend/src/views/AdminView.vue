<template>
  <div class="page">
    <h1 class="page-title">管理后台</h1>
    <p class="helper-text mt-8 mb-24">用户管理 · 系统日志排查（仅管理员可见）</p>

    <ATabs v-model="tab" :tabs="[{label:'用户管理',value:'users'},{label:'系统日志',value:'logs'}]" class="mb-24" />

    <!-- 用户管理 -->
    <template v-if="tab === 'users'">
      <div class="toolbar mb-16">
        <AInput v-model="userKeyword" placeholder="搜索用户名" class="kw" @keyup.enter="userPage = 1; loadUsers()" />
        <ASelect v-model="userRole" style="width:150px" :options="[
          {label:'全部角色',value:''},{label:'管理员',value:'admin'},{label:'普通用户',value:'normal'}
        ]" @update:model-value="userPage = 1; loadUsers()" />
        <AButton kind="secondary" @click="userPage = 1; loadUsers()">搜索</AButton>
        <span class="spacer" />
        <span class="helper-text">共 {{ usersTotal }} 个账号</span>
        <AButton @click="openCreateUser">+ 新增用户</AButton>
      </div>
      <ACard>
        <table class="table">
          <thead>
            <tr><th>ID</th><th>用户名</th><th>角色</th><th>创建时间</th><th>最后登录</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td><b>{{ u.username }}</b></td>
              <td>
                <ATag v-if="u.is_admin" text="管理员" tone="blue" />
                <ATag v-else text="普通用户" tone="gray" />
              </td>
              <td class="helper-text">{{ u.created_at }}</td>
              <td class="helper-text">{{ u.last_login_at || '—' }}</td>
              <td>
                <div style="display:flex;gap:6px">
                  <AButton kind="ghost" size="sm" @click="openReset(u)">重置密码</AButton>
                  <AButton kind="danger" size="sm" @click="removeUser(u)">删除</AButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="mt-16">
          <APagination :total="usersTotal" :page="userPage" :page-size="userPageSize" @update:page="onUserPage" />
        </div>
      </ACard>
    </template>

    <!-- 系统日志 -->
    <template v-else>
      <div class="toolbar mb-16">
        <ASelect v-model="logLevel" style="width:150px" :options="[
          {label:'全部分级',value:''},{label:'INFO',value:'INFO'},{label:'WARNING',value:'WARNING'},{label:'ERROR',value:'ERROR'}]"
          @update:model-value="logPage = 1; loadLogs()" />
        <AInput v-model="logKeyword" placeholder="关键词过滤（如 ollama / batch）" class="kw" @keyup.enter="logPage = 1; loadLogs()" />
        <AButton kind="secondary" @click="logPage = 1; loadLogs()">刷新</AButton>
        <span class="spacer" />
        <span class="helper-text">共 {{ logsTotal }} 行</span>
      </div>
      <ACard class="log-card">
        <pre class="log-pre">{{ logText }}</pre>
      </ACard>
      <div class="mt-16">
        <APagination :total="logsTotal" :page="logPage" :page-size="logPageSize" @update:page="onLogPage" />
      </div>
    </template>

    <!-- 新建用户 -->
    <AModal v-model="showCreate" title="新增用户" width="440">
      <AInput v-model="newUser.username" label="用户名（2-32 位）" />
      <div class="mt-16">
        <AInput v-model="newUser.password" label="初始密码（至少 6 位）" type="password" />
      </div>
      <div class="mt-16 admin-row">
        <span class="helper-text">设为管理员</span>
        <ASwitch v-model="newUser.is_admin" />
      </div>
      <template #footer>
        <AButton kind="secondary" @click="showCreate = false">取消</AButton>
        <AButton :loading="saving" @click="createUser">创建</AButton>
      </template>
    </AModal>

    <!-- 重置密码 -->
    <AModal v-model="showReset" :title="`重置密码 · ${resetUser?.username}`" width="420">
      <AInput v-model="resetPwd" label="新密码（至少 6 位）" type="password" />
      <template #footer>
        <AButton kind="secondary" @click="showReset = false">取消</AButton>
        <AButton :loading="saving" :disabled="resetPwd.length < 6" @click="doReset">确认重置</AButton>
      </template>
    </AModal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ACard from '../components/ui/ACard.vue'
import AInput from '../components/ui/AInput.vue'
import AButton from '../components/ui/AButton.vue'
import ATabs from '../components/ui/ATabs.vue'
import ASelect from '../components/ui/ASelect.vue'
import ATag from '../components/ui/ATag.vue'
import AModal from '../components/ui/AModal.vue'
import ASwitch from '../components/ui/ASwitch.vue'
import APagination from '../components/ui/APagination.vue'
import { api } from '../api/client'
import { toast } from '../stores/toast'
import { confirm } from '../stores/confirm'
import { useAuth } from '../stores/auth'

const auth = useAuth()
const tab = ref('users')
const users = ref([])
const usersTotal = ref(0)
const userPage = ref(1)
const userPageSize = 20
const userKeyword = ref('')
const userRole = ref('')
const logs = ref({ records: [] })
const logsTotal = ref(0)
const logPage = ref(1)
const logPageSize = 100
const logLevel = ref('')
const logKeyword = ref('')
const showCreate = ref(false)
const showReset = ref(false)
const resetUser = ref(null)
const resetPwd = ref('')
const saving = ref(false)
const newUser = reactive({ username: '', password: '', is_admin: false })

const logText = computed(() => (logs.value.records || []).join('\n') || '（暂无日志，请先产生一些操作）')

const loadUsers = async () => {
  const p = new URLSearchParams()
  p.set('page', userPage.value); p.set('page_size', userPageSize)
  if (userKeyword.value) p.set('filter_keyword', userKeyword.value)
  if (userRole.value) p.set('grade', userRole.value)
  const data = await api.adminUsers('?' + p.toString())
  users.value = data.records
  usersTotal.value = data.total
  if (userPage.value > 1 && !data.records.length) { userPage.value = 1; loadUsers() }
}
const onUserPage = (p) => { userPage.value = p; loadUsers() }

const loadLogs = async () => {
  const p = new URLSearchParams()
  p.set('page', logPage.value); p.set('page_size', logPageSize)
  if (logLevel.value) p.set('grade', logLevel.value)
  if (logKeyword.value) p.set('filter_keyword', logKeyword.value)
  const data = await api.adminLogs('?' + p.toString())
  logs.value = { records: data.records }
  logsTotal.value = data.total
  if (logPage.value > 1 && !data.records.length) { logPage.value = 1; loadLogs() }
}
const onLogPage = (p) => { logPage.value = p; loadLogs() }

const openCreateUser = () => {
  Object.assign(newUser, { username: '', password: '', is_admin: false })
  showCreate.value = true
}
const createUser = async () => {
  if (newUser.username.trim().length < 2) return toast.error('用户名至少 2 位')
  if (newUser.password.length < 6) return toast.error('密码至少 6 位')
  saving.value = true
  try {
    await api.adminCreateUser({ ...newUser, username: newUser.username.trim() })
    toast.success('用户创建成功')
    showCreate.value = false
    loadUsers()
  } finally { saving.value = false }
}
const openReset = (u) => { resetUser.value = u; resetPwd.value = ''; showReset.value = true }
const doReset = async () => {
  saving.value = true
  try {
    await api.adminResetPassword(resetUser.value.id, resetPwd.value)
    toast.success(`「${resetUser.value.username}」密码已重置`)
    showReset.value = false
  } finally { saving.value = false }
}
const removeUser = async (u) => {
  const ok = await confirm({
    title: '删除用户',
    message: `用户「${u.username}」将被删除，其生成记录仍保留。确定删除？`,
    danger: true, okText: '删除用户'
  })
  if (!ok) return
  await api.adminDeleteUser(u.id)
  toast.info('用户已删除')
  loadUsers()
}

onMounted(() => {
  if (!auth.isAdmin) {
    toast.error('需要管理员权限')
    return
  }
  loadUsers(); loadLogs()
})
</script>

<style scoped>
.spacer { flex: 1; }
.kw { width: 260px; }
.admin-row { display: flex; align-items: center; gap: 10px; }
.log-card { padding: 0; overflow: hidden; }
.log-pre {
  max-height: 60vh; overflow: auto; padding: 16px 18px;
  font-family: ui-monospace, Consolas, monospace; font-size: var(--fs-tiny);
  line-height: 1.8; color: var(--c-ink); white-space: pre-wrap; word-break: break-all;
}
</style>
