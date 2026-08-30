<template>
  <div class="page">
    <div class="head">
      <div>
        <h1 class="page-title">爆款标题 & 话题标签</h1>
        <p class="helper-text mt-8">10 组差异化标题（四类题型）+ 三层热度标签矩阵，自动去重规避同质化</p>
      </div>
      <div class="head-right">
        <ATag v-if="auth.demoMode" tone="amber" text="演示数据模式" />
      </div>
    </div>

    <ACard>
      <div class="toolbar">
        <div class="topic-input">
          <AInput v-model="topic" placeholder="输入主题，例如：AI 视频剪辑入门" />
        </div>
        <ASelect v-model="platform" style="width:170px" :options="platforms" />
        <AButton :loading="loading" @click="generate">生成标题&标签</AButton>
        <AButton v-if="result" kind="secondary" :loading="polishing" @click="polish">二次润色</AButton>
      </div>
    </ACard>

    <template v-if="loading">
      <div class="mt-24 grid-sk">
        <div v-for="i in 6" :key="i" class="skeleton" style="height:54px" />
      </div>
    </template>

    <AErrorCard v-else-if="error" :message="error" :tips="errorTips" class="mt-24">
      <AButton @click="generate">重新生成</AButton>
      <AButton kind="secondary" @click="error = ''">关闭</AButton>
    </AErrorCard>

    <template v-else-if="result">
      <!-- 操作按钮组 -->
      <div class="action-bar mt-24">
        <AButton size="sm" :loading="loading" @click="generate">🔄 重新生成</AButton>
        <AButton size="sm" kind="secondary" :loading="polishing" @click="polish">✏️ 二次润色</AButton>
        <AButton size="sm" kind="secondary" @click="exportWord">📄 导出 Word</AButton>
        <AButton size="sm" kind="secondary" @click="showSaveTpl = true">💾 保存为模板</AButton>
        <span class="spacer" />
        <ATag :text="'模型：' + result.source_model" tone="gray" />
      </div>

      <ACard class="mt-16">
        <div class="sec-head">
          <h3 class="section-title">爆款标题（{{ result.titles.length }} 组）</h3>
          <span class="spacer" />
          <CopyBtn :text="result.titles.map(t => t.title).join('\n')" />
        </div>
        <div class="title-grid mt-16">
          <div v-for="(t, i) in result.titles" :key="i" class="t-item">
            <span class="idx">{{ i + 1 }}</span>
            <span class="text">{{ t.title }}</span>
            <ATag :text="t.tone" tone="gray" />
          </div>
        </div>
      </ACard>

      <ACard class="mt-16">
        <div class="sec-head">
          <h3 class="section-title">分层话题标签</h3>
          <span class="spacer" />
          <CopyBtn :text="flatTags" />
        </div>
        <div class="tags mt-16">
          <div v-for="tier in ['hot', 'mid', 'long']" :key="tier" class="tier-row">
            <span class="tier-label">{{ tierLabel[tier] }}</span>
            <div class="tier-tags">
              <ATag v-for="(t, i) in (result.tags[tier] || [])" :key="i" :text="t" />
            </div>
          </div>
        </div>
      </ACard>

      <SaveTemplateModal v-model="showSaveTpl" default-scene="prompt"
        :default-name="`标题模板 · ${topic || '通用'}`"
        :content="result.titles.map(t => t.title).join('\n')"
        :default-description="`${result.titles.length} 组差异化标题 + 三层标签`" />
    </template>

    <AEmpty v-else class="mt-24 empty" text="生成标题与标签" hint="先输入主题，一键产出差异化标题矩阵" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import ACard from '../components/ui/ACard.vue'
import AInput from '../components/ui/AInput.vue'
import ASelect from '../components/ui/ASelect.vue'
import AButton from '../components/ui/AButton.vue'
import ATag from '../components/ui/ATag.vue'
import AEmpty from '../components/ui/AEmpty.vue'
import CopyBtn from '../components/ui/CopyBtn.vue'
import AErrorCard from '../components/AErrorCard.vue'
import SaveTemplateModal from '../components/SaveTemplateModal.vue'
import { api } from '../api/client'
import { toast } from '../stores/toast'
import { useAuth } from '../stores/auth'

const auth = useAuth()
const topic = ref('')
const platform = ref('douyin')
const loading = ref(false)
const polishing = ref(false)
const error = ref('')
const result = ref(null)
const showSaveTpl = ref(false)
const platforms = [
  { label: '抖音', value: 'douyin' }, { label: '小红书', value: 'xiaohongshu' },
  { label: '视频号', value: 'shipinhao' }, { label: '哔哩哔哩', value: 'bilibili' }
]
const tierLabel = { hot: '热门泛标签', mid: '行业中标签', long: '精准长尾标签' }
const flatTags = computed(() => Object.values(result.value?.tags || {}).flat().join(' '))
const errorTips = computed(() => [
  '确认本机 Ollama 已启动（ollama serve）或右上角配置云端 API Key',
  '标题生成对模型质量敏感，可打开右上角「演示」开关先完成演示'
])

const generate = async () => {
  if (!topic.value.trim()) return toast.error('请先输入主题')
  loading.value = true
  error.value = ''
  try {
    result.value = await api.generateTitles({ topic: topic.value.trim(), platform: platform.value, action: 'generate', demo: auth.demoMode })
    toast.success(auth.demoMode ? '演示数据已生成' : '标题&标签生成完成')
  } catch (e) {
    error.value = e.message || '生成失败'
  } finally { loading.value = false }
}
const polish = async () => {
  polishing.value = true
  error.value = ''
  try {
    result.value = await api.generateTitles({
      topic: topic.value.trim(), platform: platform.value, action: 'polish',
      existing_titles: result.value.titles.map(t => t.title), demo: auth.demoMode
    })
    toast.success('已完成二次润色')
  } catch (e) {
    error.value = e.message || '润色失败'
  } finally { polishing.value = false }
}
const exportWord = async () => {
  try {
    let url
    if (result.value.record_id) {
      url = `/api/v1/export/record/${result.value.record_id}`
    } else {
      const resp = await fetch('/api/v1/export/script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('acp_token')}` },
        body: JSON.stringify({
          topic: topic.value + ' — 标题&标签', platform: platform.value, duration: 0,
          overview: '', hook: '', segments: [], ending: '',
          titles: result.value.titles.map(t => t.title),
          title_items: result.value.titles,
          tags: Object.entries(result.value.tags).flatMap(([k, v]) => v.map(text => ({ tier: k, text }))),
          tts_text: '', body_text: '', source_model: result.value.source_model
        })
      })
      if (!resp.ok) return toast.error('导出失败')
      const blob = await resp.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob); a.download = `标题标签_${topic.value.slice(0, 20)}.docx`; a.click()
      toast.success('Word 文档已导出')
      return
    }
    const resp = await fetch(url, { headers: { Authorization: `Bearer ${localStorage.getItem('acp_token')}` } })
    if (!resp.ok) return toast.error('导出失败')
    const blob = await resp.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `标题标签_${topic.value.slice(0, 20)}.docx`
    a.click(); URL.revokeObjectURL(a.href)
    toast.success('Word 文档已导出')
  } catch { toast.error('导出失败，请重试') }
}
</script>

<style scoped>
.head { display: flex; align-items: flex-start; justify-content: space-between; }
.topic-input { flex: 1; min-width: 240px; }
.grid-sk { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.action-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; background: #fff; padding: 10px 14px; border-radius: var(--radius-md); box-shadow: var(--shadow-card); }
.spacer { flex: 1; }
.sec-head { display: flex; align-items: center; gap: 12px; }
.title-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
@media (max-width: 720px) { .title-grid { grid-template-columns: 1fr; } }
.t-item { display: flex; align-items: center; gap: 10px; background: var(--c-bg); border-radius: 10px; padding: 10px 14px; }
.idx { width: 20px; color: var(--c-gray); font-size: var(--fs-tiny); }
.text { flex: 1; font-size: var(--fs-small); }
.tags { display: flex; flex-direction: column; gap: 12px; }
.tier-row { display: flex; gap: 14px; align-items: flex-start; }
.tier-label { width: 84px; flex-shrink: 0; font-size: var(--fs-tiny); color: var(--c-gray); padding-top: 4px; }
.tier-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.empty { background: var(--c-bg); border-radius: var(--radius-lg); }
</style>
