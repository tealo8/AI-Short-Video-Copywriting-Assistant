<template>
  <div class="page">
    <!-- 首屏 Banner：极简标题 + 副标题 + 核心入口，无冗余配图 -->
    <section class="hero">
      <p class="eyebrow">AI 原生内容生产系统</p>
      <h1 class="hero-title">把创作交给 AI，<br />把时间留给灵感。</h1>
      <p class="hero-sub">输入一个主题，10 秒生成可开拍的完整短视频脚本套装：分镜脚本 · 爆款标题 · 分层标签 · 配音文稿 · 标准 Word 交付。</p>
      <div class="hero-actions">
        <AButton size="lg" @click="$router.push('/script')">立即生成脚本</AButton>
        <AButton size="lg" kind="secondary" @click="$router.push('/batch')">批量量产</AButton>
      </div>
      <div v-if="auth.status" class="provider-line helper-text">
        当前推理链路：
        <span v-for="p in auth.status.llm.providers" :key="p.provider"
          :class="['chip', p.ok ? 'on' : 'off']">{{ lbl(p.provider) }} {{ p.ok ? '✓' : '—' }}</span>
      </div>
    </section>

    <!-- 四大功能快捷入口卡片 -->
    <section class="mt-48">
      <h2 class="section-title mb-16">四大核心能力</h2>
      <div class="grid">
        <ACard v-for="f in features" :key="f.to" hover class="feature" @click="$router.push(f.to)">
          <div class="f-icon">{{ f.icon }}</div>
          <h3>{{ f.name }}</h3>
          <p class="helper-text">{{ f.desc }}</p>
          <div class="f-arrow">→</div>
        </ACard>
      </div>
    </section>

    <!-- 平台适配 + 部署模式 -->
    <section class="mt-48">
      <ACard>
        <div class="spec-row">
          <div class="spec">
            <h3>多平台风格模型化</h3>
            <p class="helper-text">抖音 / 小红书 / 视频号 / B 站，平台算法画像内置，风格自动适配</p>
          </div>
          <div class="spec">
            <h3>双模型降级链</h3>
            <p class="helper-text">Ollama 本地推理 → 云端 API → 演示兜底，7×24 小时可用</p>
          </div>
          <div class="spec">
            <h3>全链路工程容错</h3>
            <p class="helper-text">参数校验 · 超时重试 · Token 截断 · JSON 强约束 · 异常可溯源</p>
          </div>
        </div>
      </ACard>
    </section>
  </div>
</template>

<script setup>
import AButton from '../components/ui/AButton.vue'
import ACard from '../components/ui/ACard.vue'
import { useAuth } from '../stores/auth'

const auth = useAuth()
const lbl = (p) => ({ ollama: '本机 Ollama', cloud: '云端 API', mock: '演示数据' }[p] || p)

const features = [
  { to: '/script', icon: '🎬', name: '短视频脚本', desc: '结构化分镜 + 爆款钩子 + 全套标题标签，一条龙产出' },
  { to: '/copywriting', icon: '✍️', name: '智能文案编辑', desc: '六大成熟风格库：改写 / 扩写 / 缩写 / 风格迁移' },
  { to: '/batch', icon: '⚡', name: '批量量产', desc: 'TXT/Excel 导入主题清单，后台异步全套装生成' },
  { to: '/history', icon: '🗂', name: '历史与模板', desc: '记录检索复用，脚本/风格/Prompt 模板沉淀复用' }
]
</script>

<style scoped>
.hero { text-align: center; padding: 56px 0 24px; }
.eyebrow { color: var(--c-blue); font-weight: 600; font-size: var(--fs-small); letter-spacing: 0.14em; margin-bottom: 18px; }
.hero h1 { font-size: 44px; line-height: 1.25; letter-spacing: -0.02em; }
.hero-sub { max-width: 620px; margin: 22px auto 0; color: var(--c-gray); font-size: 16px; line-height: 1.8; }
.hero-actions { display: flex; gap: 14px; justify-content: center; margin-top: 32px; }
.provider-line { margin-top: 26px; display: flex; gap: 8px; justify-content: center; align-items: center; flex-wrap: wrap; }
.chip { padding: 3px 10px; border-radius: var(--radius-pill); font-size: 12px; }
.chip.on { background: rgba(52, 199, 89, 0.1); color: #248a3d; }
.chip.off { background: var(--c-bg); color: var(--c-gray); }
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
@media (max-width: 900px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 560px) { .hero h1 { font-size: 32px; } .grid { grid-template-columns: 1fr; } }
.feature { cursor: pointer; position: relative; padding: 26px; }
.f-icon { font-size: 30px; margin-bottom: 14px; }
.feature h3 { font-size: 16px; margin-bottom: 8px; }
.feature p { line-height: 1.7; }
.f-arrow { position: absolute; top: 26px; right: 24px; color: var(--c-gray); opacity: 0; transition: all var(--t-base) var(--ease); }
.feature:hover .f-arrow { opacity: 1; transform: translateX(3px); }
.spec-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.spec h3 { font-size: 15px; margin-bottom: 6px; }
@media (max-width: 800px) { .spec-row { grid-template-columns: 1fr; } }
</style>
