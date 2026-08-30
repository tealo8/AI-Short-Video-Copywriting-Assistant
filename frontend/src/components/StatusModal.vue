<template>
  <AModal :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)"
    title="系统状态" width="620">
    <!-- 模型链 -->
    <div class="mb-16">
      <h4 class="sub">模型推理链（{{ auth.status?.llm?.chain?.join(' → ') || '检测中' }}）</h4>
      <div v-for="(p, i) in (auth.status?.llm?.providers || [])" :key="p.provider" class="row">
        <span class="dot" :class="p.ok ? 'ok' : 'err'" />
        <span class="name">{{ name(p.provider) }}</span>
        <span class="detail helper-text">{{ p.detail }}</span>
      </div>
    </div>

    <div class="row">
      <span class="dot ok" />
      <span class="name">数据库</span>
      <span class="detail helper-text">{{ auth.status?.db === 'ok' ? 'SQLite 连接正常（WAL 并发模式）' : '未知' }}</span>
    </div>
    <div class="row">
      <span class="dot" :class="auth.status ? 'ok' : 'err'" />
      <span class="name">前端-后端通道</span>
      <span class="detail helper-text">{{ auth.status ? 'API 连接正常' : '无法连接后端服务' }}</span>
    </div>

    <h4 class="sub mt-24">排查指引</h4>
    <ul class="tips">
      <li>Ollama 红点：运行 <code>ollama serve</code> 并 <code>ollama pull qwen2.5:7b</code>（或在「模型配置」修改地址/模型名）</li>
      <li>云端红点：在「模型配置」填写 CLOUD_API_KEY（支持 DeepSeek / 通义 / OpenAI 兼容接口）</li>
      <li>演示模式：全部模型不可达时自动开启，结果不调用大模型，可直接用于演示</li>
    </ul>
  </AModal>
</template>

<script setup>
import AModal from './ui/AModal.vue'
import { useAuth } from '../stores/auth'
defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue'])
const auth = useAuth()
const name = (p) => ({ ollama: '本地 Ollama', cloud: '云端 API', mock: '演示数据' }[p] || p)
</script>

<style scoped>
.sub { font-size: 14px; font-weight: 700; margin-bottom: 10px; }
.row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--c-line); }
.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot.ok { background: var(--c-green); }
.dot.err { background: var(--c-red); }
.name { font-weight: 600; width: 104px; flex-shrink: 0; font-size: var(--fs-small); }
.detail { flex: 1; }
.tips { padding-left: 18px; color: var(--c-gray); font-size: var(--fs-small); line-height: 2; }
code { background: var(--c-bg); padding: 1px 6px; border-radius: 5px; }
</style>
