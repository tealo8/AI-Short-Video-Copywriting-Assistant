<template>
  <div>
    <!-- 全局降级/状态提示条 -->
    <transition name="banner">
      <div v-if="banner" class="global-banner" :class="banner.tone" @click="openStatus">
        {{ banner.text }} <span class="link">查看详情 →</span>
      </div>
    </transition>

    <ANavbar />
    <router-view v-slot="{ Component }">
      <transition name="page" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <AFooter />
    <AToast />
    <ConfirmDialog />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import ANavbar from './components/ui/ANavbar.vue'
import AFooter from './components/ui/AFooter.vue'
import AToast from './components/ui/AToast.vue'
import ConfirmDialog from './components/ui/ConfirmDialog.vue'
import StatusModal from './components/StatusModal.vue'
import { useAuth } from './stores/auth'

const route = useRoute()
const auth = useAuth()
const showStatus = ref(false)

let timer = null
const refresh = async () => { await auth.refreshStatus() }
onMounted(() => { refresh(); timer = setInterval(refresh, 30000) })
onBeforeUnmount(() => clearInterval(timer))

const providers = computed(() => auth.status?.llm?.providers || [])
const active = computed(() => auth.status?.llm?.active_provider || '')

/** 降级提示条：云端不可用切换本地 / 全部降级到演示 / 云端主用 */
const banner = computed(() => {
  if (!auth.status) return null
  const byName = Object.fromEntries(providers.value.map(p => [p.provider, p]))
  if (auth.demoMode) {
    return { tone: 'info', text: '演示数据模式：结果来自预置示例，不调用大模型（关闭右上角开关恢复真实生成）' }
  }
  if (active.value === 'mock') {
    return { tone: 'warn', text: '大模型目前不可达（Ollama 未启动 / 云端 Key 未配置），系统已降级为演示数据模式' }
  }
  if (active.value === 'ollama' && byName.cloud && !byName.cloud.ok) {
    return { tone: 'info', text: '云端 API 不可用或未配置，已自动切换本地 Ollama 模型' }
  }
  if (active.value === 'cloud' && byName.ollama && !byName.ollama.ok) {
    return { tone: 'info', text: '本地 Ollama 不可用，已自动切换云端模型' }
  }
  return null
})

const openStatus = () => { showStatus.value = true; refresh() }
</script>

<style scoped>
.global-banner {
  position: relative; z-index: 60;
  text-align: center; font-size: var(--fs-small); padding: 7px 16px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.global-banner.info { background: rgba(0, 113, 227, 0.1); color: var(--c-blue); }
.global-banner.warn { background: rgba(255, 159, 10, 0.14); color: #b26a00; }
.link { opacity: 0.8; }
.page-enter-active, .page-leave-active { transition: opacity var(--t-base) ease; }
.page-enter-from, .page-leave-to { opacity: 0; }
.banner-enter-active, .banner-leave-active { transition: all var(--t-base) ease; }
.banner-enter-from, .banner-leave-to { transform: translateY(-100%); }
</style>
