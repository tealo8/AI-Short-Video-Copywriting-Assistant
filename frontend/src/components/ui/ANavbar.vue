<template>
  <header class="a-nav" :class="{ solid: scrolled }">
    <nav class="nav-inner">
      <router-link to="/" class="brand">
        <span class="logo">✳️</span>
        <span class="brand-name">AI 内容工场</span>
      </router-link>

      <div class="links">
        <template v-if="auth.isLoggedIn">
          <router-link v-for="l in links" :key="l.to" :to="l.to" class="link"
            :class="{ active: route.path === l.to }">{{ l.label }}</router-link>
          <router-link v-if="auth.isAdmin" to="/admin" class="link"
            :class="{ active: route.path === '/admin' }">管理</router-link>
        </template>
      </div>

      <div class="right">
        <!-- 模型状态点：点击打开状态弹窗 -->
        <button class="status-chip" @click="showStatus = true" title="点击查看模型链状态">
          <span class="status-dot" :class="statusClass" />
          {{ providerLabel }}
        </button>

        <!-- 演示数据开关 -->
        <label class="demo-switch" title="演示数据：不调用大模型，输出预置示例（面试演示防翻车）">
          <span class="helper-text">演示</span>
          <ASwitch :model-value="auth.demoMode" @update:model-value="toggleDemo" />
        </label>

        <template v-if="auth.isLoggedIn">
          <span class="user" @click="showPwd = true" title="修改密码">{{ auth.user?.username }}</span>
          <button class="login-btn" @click="logout">退出</button>
        </template>
      </div>
    </nav>

    <!-- 弹窗 -->
    <ModelConfigModal v-model="showConfig" />
    <StatusModal v-model="showStatus" />
    <ChangePasswordModal v-model="showPwd" />
  </header>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ASwitch from './ASwitch.vue'
import ModelConfigModal from '../ModelConfigModal.vue'
import StatusModal from '../StatusModal.vue'
import ChangePasswordModal from '../ChangePasswordModal.vue'
import { useAuth } from '../../stores/auth'
import { toast } from '../../stores/toast'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const scrolled = ref(false)
const showConfig = ref(false)
const showStatus = ref(false)
const showPwd = ref(false)

const onScroll = () => { scrolled.value = window.scrollY > 12 }
onMounted(() => { window.addEventListener('scroll', onScroll); onScroll(); auth.refreshStatus() })
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const links = [
  { to: '/', label: '首页' },
  { to: '/script', label: '脚本生成' },
  { to: '/titles', label: '标题标签' },
  { to: '/copywriting', label: '文案改写' },
  { to: '/batch', label: '批量生成' },
  { to: '/history', label: '历史记录' },
  { to: '/templates', label: '模板库' }
]

const activeProvider = computed(() => auth.status?.llm?.active_provider || '')
const statusClass = computed(() => {
  if (!auth.status) return 'warn'
  const p = (auth.status.llm?.providers || []).find(x => x.provider === activeProvider.value)
  return p?.ok ? 'ok' : 'warn'
})
const providerLabel = computed(() => {
  if (auth.demoMode) return '演示模式'
  const map = { ollama: '本地 Ollama', cloud: '云端模型', mock: '演示模式' }
  return activeProvider.value ? map[activeProvider.value] || activeProvider.value : '检测中'
})

const toggleDemo = async (v) => {
  auth.setDemo(v)
  toast.info(v ? '演示数据模式已开启：结果来自预置示例' : '演示数据模式已关闭')
}
const logout = () => { auth.logout(); router.push('/login') }
</script>

<style scoped>
.a-nav {
  position: sticky; top: 0; z-index: 50;
  backdrop-filter: saturate(180%) blur(20px);
  background: rgba(255, 255, 255, 0.72);
  transition: background var(--t-base) var(--ease), box-shadow var(--t-base) var(--ease);
}
.a-nav.solid { box-shadow: var(--shadow-nav); background: rgba(255, 255, 255, 0.86); }
.nav-inner {
  max-width: 1080px; margin: 0 auto; padding: 0 32px;
  height: 52px; display: flex; align-items: center; gap: 22px;
}
.brand { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 15px; letter-spacing: -0.01em; }
.logo { font-size: 17px; }
.links { display: flex; gap: 4px; flex: 1; }
.link {
  padding: 7px 10px; border-radius: 8px; font-size: var(--fs-small); color: var(--c-gray);
  transition: color var(--t-fast) var(--ease), background var(--t-fast) var(--ease);
}
.link:hover { color: var(--c-ink); }
.link.active { color: var(--c-ink); font-weight: 600; }
.right { display: flex; align-items: center; gap: 12px; }
.status-chip {
  display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px;
  background: var(--c-bg); border-radius: var(--radius-pill); font-size: var(--fs-tiny);
  color: var(--c-gray); cursor: pointer; transition: background var(--t-fast) var(--ease);
}
.status-chip:hover { background: #eef0f2; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; }
.status-dot.ok { background: var(--c-green); }
.status-dot.warn { background: var(--c-amber); }
.demo-switch { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; }
.user {
  font-size: var(--fs-small); color: var(--c-gray); cursor: pointer;
  padding: 5px 8px; border-radius: 8px; transition: background var(--t-fast);
}
.user:hover { background: var(--c-bg); color: var(--c-ink); }
.login-btn {
  padding: 6px 14px; border-radius: var(--radius-pill); background: var(--c-blue); color: #fff;
  font-size: var(--fs-small); font-weight: 500; transition: background var(--t-base) var(--ease);
}
.login-btn:hover { background: var(--c-blue-hover); }
@media (max-width: 960px) { .links { display: none; } }
</style>
