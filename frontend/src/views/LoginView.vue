<template>
  <div class="login-page">
    <div class="login-card">
      <div class="logo-zone">
        <span class="logo">✳️</span>
        <h1 class="hero-title">AI 内容工场</h1>
        <p class="helper-text">一站式短视频&文案智能生产平台</p>
      </div>

      <div class="form">
        <AInput v-model="username" label="用户名" placeholder="2-32 位字符" :hint="error || ''" :error="!!error" />
        <div class="mt-16">
          <AInput v-model="password" label="密码" type="password" placeholder="请输入密码"
            @keyup.enter="submit" />
        </div>
        <AButton class="mt-32" size="lg" style="width:100%" :loading="loading" @click="submit">
          登 录
        </AButton>
      </div>

      <p class="helper-text center mt-24">
        初始管理员：admin / admin123（首次启动自动创建，登录后请尽快修改密码）
      </p>
      <p class="helper-text center mt-8">本地化部署 · 数据不出内网 · 支持 Ollama 离线推理</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AInput from '../components/ui/AInput.vue'
import AButton from '../components/ui/AButton.vue'
import { useAuth } from '../stores/auth'
import { toast } from '../stores/toast'

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const auth = useAuth()
const router = useRouter()
const route = useRoute()

const submit = async () => {
  error.value = ''
  if (username.value.trim().length < 2) { error.value = '用户名至少 2 位'; return }
  if (password.value.length < 6) { error.value = '密码至少 6 位'; return }
  loading.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    toast.success('欢迎回来')
    router.push(route.query.redirect || '/')
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(180deg, #fff 0%, var(--c-bg) 100%); padding: 24px;
}
.login-card {
  width: 100%; max-width: 400px; background: #fff; border-radius: 24px;
  padding: 44px 40px 36px; box-shadow: var(--shadow-hover);
}
.logo-zone { text-align: center; margin-bottom: 32px; }
.logo { font-size: 40px; display: block; margin-bottom: 12px; }
.logo-zone .hero-title { font-size: 24px; }
.logo-zone .helper-text { margin-top: 6px; }
.center { text-align: center; }
</style>
