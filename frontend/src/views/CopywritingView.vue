<template>
  <div class="page">
    <div class="head">
      <div>
        <h1 class="page-title">智能文案编辑器</h1>
        <p class="helper-text mt-8">改写 / 扩写 / 缩写 / 风格迁移 / 润色 / 纠错 / 原创度提升，六大风格库即选即用</p>
      </div>
      <div class="head-right">
        <ATag v-if="auth.demoMode" tone="amber" text="演示数据模式" />
      </div>
    </div>

    <div class="toolbar mb-16" style="justify-content: center">
      <ATabs v-model="action" :tabs="actionTabs" />
    </div>
    <div class="toolbar mb-24" style="justify-content: center">
      <div class="style-select">
        <ASelect v-model="style" label="" :options="styleOptions" />
      </div>
      <AInput v-if="style === '自定义'" v-model="customStyle" placeholder="描述你的自定义风格要求" class="custom" />
    </div>

    <div class="split">
      <!-- 左侧输入 -->
      <ACard class="editor">
        <div class="sec-head">
          <h3 class="section-title">原文</h3>
          <span class="spacer" />
          <span class="helper-text" :class="{ over: text.length >= 5000 }">{{ text.length }} / 5000 字</span>
        </div>
        <textarea v-model="text" class="editor-area" :maxlength="5000"
          placeholder="粘贴需要处理的文案 / 脚本 / 口播稿…（最多 5000 字）" />
        <p v-if="text.length >= 5000" class="over-tip">输入内容已到达最大长度（5000 字），请精简后提交</p>
        <div class="toolbar mt-16">
          <AButton :loading="loading" @click="run">✨ 开始处理</AButton>
          <AButton kind="secondary" @click="text = ''">清空</AButton>
        </div>
      </ACard>

      <!-- 右侧结果 -->
      <ACard class="editor result">
        <div class="sec-head">
          <h3 class="section-title">处理结果</h3>
          <span class="spacer" />
          <!-- 操作按钮组 -->
          <AButton size="sm" :loading="loading" @click="run">🔄 重新处理</AButton>
          <AButton size="sm" kind="secondary" @click="showSaveTpl = true">💾 保存为模板</AButton>
          <AButton size="sm" kind="secondary" @click="exportWord">📄 导出 Word</AButton>
          <CopyBtn v-if="result" :text="result.result" />
        </div>
        <div v-if="loading" class="skeleton" style="height: 260px" />
        <AErrorCard v-else-if="error" :message="error" :tips="errorTips" class="mt-16">
          <AButton @click="run">重试</AButton>
        </AErrorCard>
        <div v-else-if="result" class="result-body">
          <p>{{ result.result }}</p>
          <div class="key-points mt-16">
            <span class="helper-text">亮点拆解：</span>
            <ATag v-for="(k, i) in result.key_points" :key="i" :text="k" tone="green" />
          </div>
          <div class="helper-text mt-8">
            差异度 {{ result.changed_count }}% · 模型 {{ result.source_model }}
            · 已自动保存至历史
          </div>
        </div>
        <AEmpty v-else text="等待处理" hint="左侧粘贴原文 → 选择动作与风格 → 开始处理" />

        <SaveTemplateModal v-model="showSaveTpl" default-scene="style"
          :default-name="`风格模板 · ${styleLabel}`"
          :content="result?.result || ''" :default-description="`${actionLabel} · ${styleLabel}`" />
      </ACard>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import ACard from '../components/ui/ACard.vue'
import AInput from '../components/ui/AInput.vue'
import AButton from '../components/ui/AButton.vue'
import ATabs from '../components/ui/ATabs.vue'
import ASelect from '../components/ui/ASelect.vue'
import ATag from '../components/ui/ATag.vue'
import AEmpty from '../components/ui/AEmpty.vue'
import CopyBtn from '../components/ui/CopyBtn.vue'
import AErrorCard from '../components/AErrorCard.vue'
import SaveTemplateModal from '../components/SaveTemplateModal.vue'
import { api } from '../api/client'
import { toast } from '../stores/toast'
import { useAuth } from '../stores/auth'

const auth = useAuth()
const action = ref('rewrite')
const style = ref('通用')
const customStyle = ref('')
const text = ref('')
const loading = ref(false)
const error = ref('')
const result = ref(null)
const showSaveTpl = ref(false)

const actionTabs = [
  { label: '智能润色', value: 'rewrite' },
  { label: '扩写丰富', value: 'expand' },
  { label: '精炼缩写', value: 'condense' },
  { label: '风格迁移', value: 'style_transfer' },
  { label: '逻辑重构', value: 'polish' },
  { label: '纠错校对', value: 'proofread' },
  { label: '原创度提升', value: 'dedupe' }
]
const styleOptions = [
  { label: '通用', value: '通用' },
  { label: '小红书温柔种草风', value: '小红书温柔种草风' },
  { label: '抖音口播干货风', value: '抖音口播干货风' },
  { label: '正式专业科普风', value: '正式专业科普风' },
  { label: '幽默轻松段子风', value: '幽默轻松段子风' },
  { label: '电商带货营销风', value: '电商带货营销风' },
  { label: '极简高级短句风', value: '极简高级短句风' },
  { label: '自定义风格…', value: '自定义' }
]
const actionLabel = computed(() => actionTabs.find(t => t.value === action.value)?.label || action.value)
const styleLabel = computed(() => style.value === '自定义' ? (customStyle.value || '自定义') : style.value)
const errorTips = computed(() => [
  '确认本机 Ollama 已启动或在右上角配置云端 API Key',
  '原文需 10-5000 字，当前字数超限时请精简',
  '演示模式可零模型验证本功能（右上角开关）'
])

watch(style, v => { if (v === '自定义') customStyle.value = customStyle.value || '' })

onMounted(() => {
  // 模板库「使用风格模板」带入
  const s = sessionStorage.getItem('acp_copy_style')
  if (s) {
    sessionStorage.removeItem('acp_copy_style')
    customStyle.value = s
    style.value = '自定义'
    toast.info('已带入模板设定的风格要求，粘贴原文即可处理')
  }
})

const run = async () => {
  if (text.value.trim().length < 10) return toast.error('原文至少 10 字')
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.transformCopy({
      text: text.value.trim(), action: action.value, style: style.value,
      custom_style: style.value === '自定义' ? customStyle.value : '',
      demo: auth.demoMode
    })
    toast.success(auth.demoMode ? '演示数据已生成' : '文案处理完成')
  } catch (e) {
    error.value = e.message || '处理失败'
  } finally { loading.value = false }
}

const exportWord = async () => {
  try {
    const url = result.value?.record_id
      ? `/api/v1/export/record/${result.value.record_id}`
      : null
    if (!url) return toast.error('演示数据未落库，请关闭演示模式并重新处理后导出')
    const resp = await fetch(url, { headers: { Authorization: `Bearer ${localStorage.getItem('acp_token')}` } })
    if (!resp.ok) return toast.error('导出失败')
    const blob = await resp.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `文案_${actionLabel.value}.docx`
    a.click(); URL.revokeObjectURL(a.href)
    toast.success('Word 文档已导出')
  } catch { toast.error('导出失败，请重试') }
}
</script>

<style scoped>
.head { display: flex; align-items: flex-start; justify-content: space-between; }
.head-right { display: flex; gap: 8px; }
.style-select { width: 240px; }
.custom { width: 340px; }
.split { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: stretch; }
@media (max-width: 880px) { .split { grid-template-columns: 1fr; } }
.sec-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.spacer { flex: 1; }
.editor { display: flex; flex-direction: column; }
.editor-area {
  flex: 1; min-height: 300px; border: none; outline: none; resize: vertical;
  background: var(--c-bg); border-radius: var(--radius-md); padding: 18px;
  font-size: var(--fs-body); line-height: 1.9; color: var(--c-ink); margin-top: 14px;
}
.editor-area:focus { box-shadow: 0 0 0 3px var(--c-blue-soft); }
.over-tip { color: var(--c-red); font-size: var(--fs-tiny); margin-top: 6px; }
.over { color: var(--c-red) !important; }
.result-body { padding: 18px 0; }
.result-body p { white-space: pre-wrap; line-height: 1.9; font-size: var(--fs-body); }
.key-points { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
</style>
