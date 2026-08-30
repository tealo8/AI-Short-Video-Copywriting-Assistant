<template>
  <div class="page">
    <div class="head">
      <div>
        <h1 class="page-title">AI 短视频脚本</h1>
        <p class="helper-text mt-8">输入主题，输出可开拍的完整套装：分镜 · 钩子 · 标题 · 标签 · 配音稿</p>
      </div>
      <div class="head-right">
        <ATag v-if="auth.demoMode" tone="amber" text="演示数据模式" />
        <ATag v-if="result?.source_model" tone="gray" :text="'模型：' + result.source_model" />
      </div>
    </div>

    <div class="layout">
      <!-- 左侧：参数配置 -->
      <aside class="left">
        <ACard>
          <ATextarea v-model="form.topic" label="视频主题" :rows="3" count :maxlength="100"
            placeholder="例如：普通人如何用 AI 工具副业变现" hint="主题越具体，脚本越精准（2-100 字）" />
          <div class="mt-16">
            <ASelect v-model="form.platform" label="目标平台" :options="platforms" />
          </div>
          <div class="mt-16">
            <ASelect v-model="form.style" label="内容风格" :options="styles" />
          </div>
          <div class="mt-16">
            <AInput v-model="form.custom_style" label="自定义风格要求（可选）"
              placeholder="例如：口语化一点，多聊真实案例" />
          </div>
          <div class="mt-16">
            <label class="a-label">视频时长</label>
            <div class="durations">
              <button v-for="d in durations" :key="d" class="dur" :class="{ on: form.duration === d }"
                @click="form.duration = d">{{ d }}s</button>
            </div>
          </div>
          <div class="mt-16">
            <label class="a-label">口播字数范围（可选约束）</label>
            <div class="budget">
              <AInput v-model.number="form.word_budget_min" placeholder="下限" type="number" />
              <span class="helper-text">—</span>
              <AInput v-model.number="form.word_budget_max" placeholder="上限" type="number" />
            </div>
            <p class="helper-text mt-8">留空则按时长自动计算（约 4 字/秒）；冲突时提示不发起请求</p>
          </div>
          <AButton class="mt-24 lg-block" size="lg" :loading="loading" @click="generate">
            {{ loading ? 'AI 创作中…' : (auth.demoMode ? '✨ 生成演示脚本' : '✨ 生成完整脚本') }}
          </AButton>
          <p class="helper-text mt-16 center" v-if="!auth.demoMode">预计耗时 {{ expectText }} · 全链路容错保护</p>
          <p class="helper-text mt-16 center" v-else>演示模式不调用大模型，毫秒级返回示例</p>
        </ACard>
      </aside>

      <!-- 右侧：结果区 -->
      <main class="right">
        <!-- 骨架屏 -->
        <div v-if="loading" class="gen-skeleton">
          <div class="skeleton" style="height: 90px" />
          <div class="skeleton" style="height: 64px" />
          <div class="skeleton" style="height: 190px" />
          <div class="skeleton" style="height: 80px" />
          <p class="helper-text center mt-16">
            {{ auth.demoMode ? '正在生成演示数据…' : '本地模型正在启动时首次调用较慢，请稍候（约 15-90 秒）…' }}
          </p>
        </div>

        <!-- 错误态 -->
        <AErrorCard v-else-if="error" :message="error" :tips="errorTips">
          <AButton @click="generate">重新生成</AButton>
          <AButton kind="secondary" @click="error = ''">关闭</AButton>
        </AErrorCard>

        <template v-else-if="result">
          <div v-if="result.warnings?.length" class="warn-box">
            <span class="helper-text" style="color:#b26a00">质检提示：</span>
            <span v-for="(w, i) in result.warnings" :key="i" class="helper-text">{{ w }}</span>
          </div>

          <!-- 操作按钮组 -->
          <div class="action-bar">
            <span v-if="result.topic" class="topic-chip" :title="'当前主题：' + result.topic">📌 {{ result.topic }}</span>
            <AButton size="sm" :loading="loading" @click="generate">🔄 重新生成</AButton>
            <AButton size="sm" kind="secondary" @click="openFineTune">✏️ 局部微调</AButton>
            <AButton size="sm" kind="secondary" @click="exportWord">📄 导出 Word</AButton>
            <AButton size="sm" kind="secondary" @click="showSaveTpl = true">💾 保存为模板</AButton>
            <AButton size="sm" kind="secondary" @click="saveHistory">🗂 保存至历史</AButton>
            <span class="spacer" />
            <span class="helper-text">Word 内已定义标题/小标题/正文的样式规范，交付级排版</span>
          </div>

          <!-- 概览 -->
          <ACard class="mt-16">
            <div class="sec-head">
              <h3 class="section-title">主题概述</h3>
              <span class="spacer" />
              <CopyBtn :text="result.overview" />
            </div>
            <div class="plain mt-12">{{ result.overview }}</div>
            <div class="hook mt-12">{{ result.hook }}
              <span class="hook-tag">3 秒钩子</span>
              <CopyBtn class="ml8" :text="result.hook" />
            </div>
          </ACard>

          <!-- 四 Tab 分区 -->
          <ATabs v-model="tab" class="mt-16" :tabs="tabs" />

          <!-- 分镜脚本 -->
          <ACard v-if="tab === 'segments'" class="mt-16">
            <div class="sec-head">
              <h3 class="section-title">分镜脚本（{{ result.segments.length }} 段）</h3>
              <span class="spacer" />
              <CopyBtn :text="segmentsAsText" />
            </div>
            <div class="table-scroll mt-16">
              <table class="table">
                <thead>
                  <tr><th>#</th><th>时间</th><th>类型</th><th>画面内容</th><th>出镜台词</th><th>字幕重点</th><th></th></tr>
                </thead>
                <tbody>
                  <tr v-for="seg in result.segments" :key="seg.index">
                    <td>{{ seg.index }}</td>
                    <td class="nowrap">{{ seg.start_time }}–{{ seg.end_time }}</td>
                    <td class="type-cell"><ATag :text="seg.type === 'on_camera' ? '出镜' : '旁白'" :tone="seg.type === 'on_camera' ? 'green' : 'gray'" /></td>
                    <td class="scene">{{ seg.scene }}</td>
                    <td class="lines">{{ seg.lines }}</td>
                    <td class="subtitle">{{ seg.subtitle }}</td>
                    <td><CopyBtn :text="seg.lines" /></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </ACard>

          <!-- 标题 -->
          <ACard v-else-if="tab === 'titles'" class="mt-16">
            <div class="sec-head">
              <h3 class="section-title">爆款标题（{{ result.titles.length }} 组）</h3>
              <span class="spacer" />
              <CopyBtn :text="(result.titles || []).join('\n')" />
            </div>
            <div class="title-grid mt-16">
              <div v-for="(t, i) in result.title_items" :key="i" class="title-item">
                <span class="idx">{{ i + 1 }}</span>
                <span class="t-text">{{ t.title }}</span>
                <ATag :text="t.tone" tone="gray" />
                <CopyBtn :text="t.title" />
              </div>
            </div>
          </ACard>

          <!-- 标签 -->
          <ACard v-else-if="tab === 'tags'" class="mt-16">
            <div class="sec-head">
              <h3 class="section-title">话题标签矩阵</h3>
              <span class="spacer" />
              <CopyBtn :text="tagsFlatText" />
            </div>
            <div class="tags-wrap mt-16">
              <div v-for="tier in ['hot', 'mid', 'long']" :key="tier" class="tier-row">
                <span class="tier-label">{{ tierLabel[tier] }}</span>
                <div class="tier-tags">
                  <ATag v-for="(t, i) in result.tags.filter(x => x.tier === tier)" :key="i" :text="t.text" />
                </div>
              </div>
            </div>
          </ACard>

          <!-- TTS 配音文稿 -->
          <ACard v-else class="mt-16">
            <div class="sec-head">
              <h3 class="section-title">TTS 配音文稿</h3>
              <span class="spacer" />
              <span class="helper-text">
                {{ result.tts_meta?.total_chars }} 字 · 约 {{ result.tts_meta?.est_duration_sec }}s 朗读 ·
                {{ result.tts_meta?.mode === 'on_camera' ? '出镜口播' : '旁白配音' }}
              </span>
              <CopyBtn :text="result.tts_text" />
            </div>
            <div class="tts-block mt-16">
              <p v-for="(s, i) in result.tts_meta?.sentences" :key="i">{{ s }}</p>
            </div>
            <p class="helper-text mt-12">已自动剔除书面语/填充词、长句断句并标注停顿，可直接复制进剪映 AI 配音</p>
          </ACard>

          <!-- 结尾互动 -->
          <ACard class="mt-16">
            <div class="sec-head">
              <h3 class="section-title">结尾互动引导</h3>
              <span class="spacer" />
              <CopyBtn :text="result.ending" />
            </div>
            <div class="plain mt-12">{{ result.ending }}</div>
          </ACard>
          <!-- 说明：局部微调 弹窗 -->
          <AModal v-model="showFineTune" title="局部微调" width="520">
            <p class="helper-text mb-8">描述你想调整的内容（仅基于当前主题重新生成，不会清空表单）：</p>
            <ATextarea v-model="fineTuneText" :rows="4" placeholder="例如：开头的钩子改得更夸张一点；第三段加一个真实案例；结尾互动改成引导评论区留言" />
            <template #footer>
              <AButton kind="secondary" @click="showFineTune = false">取消</AButton>
              <AButton :loading="loading" @click="applyFineTune">按此要求重新生成</AButton>
            </template>
          </AModal>

          <SaveTemplateModal v-model="showSaveTpl" default-scene="script"
            :default-name="`脚本模板 · ${result.topic}`"
            :content="result.body_text" :default-description="`${result.duration}s / ${result.style}`" />
        </template>

        <AEmpty v-else text="等待生成" hint="在左侧输入主题，点击「生成完整脚本」开始创作"
          class="empty-card" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ACard from '../components/ui/ACard.vue'
import ATextarea from '../components/ui/ATextarea.vue'
import ASelect from '../components/ui/ASelect.vue'
import AInput from '../components/ui/AInput.vue'
import AButton from '../components/ui/AButton.vue'
import ATag from '../components/ui/ATag.vue'
import AEmpty from '../components/ui/AEmpty.vue'
import ATabs from '../components/ui/ATabs.vue'
import AModal from '../components/ui/AModal.vue'
import CopyBtn from '../components/ui/CopyBtn.vue'
import AErrorCard from '../components/AErrorCard.vue'
import SaveTemplateModal from '../components/SaveTemplateModal.vue'
import { api } from '../api/client'
import { toast } from '../stores/toast'
import { useAuth } from '../stores/auth'

const auth = useAuth()
const loading = ref(false)
const error = ref('')
const result = ref(null)
const tab = ref('segments')
const showFineTune = ref(false)
const fineTuneText = ref('')
const showSaveTpl = ref(false)
const form = reactive({
  topic: '', platform: 'douyin', style: '通用', custom_style: '',
  duration: 60, word_budget_min: null, word_budget_max: null
})

const platforms = [
  { label: '抖音 · 快节奏强钩子', value: 'douyin' },
  { label: '小红书 · 种草分享感', value: 'xiaohongshu' },
  { label: '视频号 · 理性价值向', value: 'shipinhao' },
  { label: '哔哩哔哩 · 硬核干货向', value: 'bilibili' }
]
const styles = [
  { label: '通用', value: '通用' },
  { label: '小红书温柔种草风', value: '小红书温柔种草风' },
  { label: '抖音口播干货风', value: '抖音口播干货风' },
  { label: '正式专业科普风', value: '正式专业科普风' },
  { label: '幽默轻松段子风', value: '幽默轻松段子风' },
  { label: '电商带货营销风', value: '电商带货营销风' },
  { label: '极简高级短句风', value: '极简高级短句风' }
]
const durations = [30, 60, 90, 120, 180]
const tabs = [
  { label: '分镜脚本', value: 'segments' },
  { label: '爆款标题', value: 'titles' },
  { label: '话题标签', value: 'tags' },
  { label: 'TTS 配音文稿', value: 'tts' }
]
const tierLabel = { hot: '热门泛标签', mid: '行业中标签', long: '精准长尾标签' }
const expectText = computed(() => (form.duration <= 60 ? '30-60 秒' : '1-3 分钟'))
const segmentsAsText = computed(() =>
  (result.value?.segments || []).map(s => `[${s.start_time}-${s.end_time}] ${s.lines}`).join('\n'))
const tagsFlatText = computed(() =>
  (result.value?.tags || []).map(t => t.text).join(' '))
const errorTips = computed(() => {
  if (!error.value) return []
  const tips = []
  if (/Ollama|模型|Provider|2001|502/i.test(error.value)) {
    tips.push('确认本机 Ollama 服务已启动：ollama serve')
    tips.push('确认模型已拉取：ollama pull qwen2.5:7b（可在右上角「模型配置」修改）')
    tips.push('或填写云端 API Key 自动降级（右上角「模型配置」）')
  }
  if (/超时|timeout|Timeout/i.test(error.value)) tips.push('生成超时：本地模型冷启动较慢，请重试一次')
  if (/参数校验|1001/i.test(error.value)) tips.push('检查输入参数：主题 2-100 字、时长 10-300 秒、字数范围合法')
  tips.push('演示模式开关已就绪：开启后无需任何模型即可完成演示')
  return tips.slice(0, 4)
})

const validate = () => {
  if (!form.topic.trim()) { toast.error('请先输入视频主题'); return false }
  const { word_budget_min: lo, word_budget_max: hi } = form
  if (lo && hi && lo > hi) { toast.error('字数下限不能大于上限，请调整'); return false }
  if ((lo && lo < 20) || (hi && hi > 1000)) { toast.error('字数范围需在 20-1000 之间'); return false }
  return true
}

const generate = async () => {
  if (!validate()) return
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.generateScript({ ...form, topic: form.topic.trim(), demo: auth.demoMode })
    if (auth.demoMode) toast.success('演示脚本生成完成（未调用大模型）')
    else toast.success('脚本生成完成')
  } catch (e) {
    error.value = e.message || '生成失败，请稍后重试'
  } finally { loading.value = false }
}

const applyFineTune = async () => {
  if (!fineTuneText.value.trim()) return toast.error('请描述你的微调要求')
  showFineTune.value = false
  const custom = `（用户在以下方向微调：${fineTuneText.value.trim()}）。务必按此要求修改，其余保持。`
  loading.value = true
  error.value = ''
  try {
    result.value = await api.generateScript({
      ...form, topic: form.topic.trim(), demo: auth.demoMode, custom_style: custom
    })
    toast.success('已按微调要求重新生成')
    fineTuneText.value = ''
  } catch (e) {
    error.value = e.message || '微调失败，请稍后重试'
  } finally { loading.value = false }
}

const saveHistory = () => {
  if (result.value?.record_id) {
    toast.success('本次生成已保存至历史记录，可随时复用')
  } else if (auth.demoMode) {
    toast.info('演示数据未落库；关闭演示开关重新生成即可自动保存')
  } else {
    toast.info('记录已自动保存，可在「历史记录」页查看')
  }
}

const exportWord = async (silent = false) => {
  try {
    const resp = await fetch('/api/v1/export/script', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('acp_token')}` },
      body: JSON.stringify(result.value)
    })
    if (!resp.ok) { toast.error('Word 导出失败'); return }
    const blob = await resp.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `短视频脚本_${result.value.topic.slice(0, 24)}.docx`
    a.click()
    URL.revokeObjectURL(a.href)
    toast.success('Word 文档已导出（标题/小标题/正文样式已规范定义）')
  } catch { toast.error('Word 导出失败') }
}

const openFineTune = () => { fineTuneText.value = ''; showFineTune.value = true }

onMounted(() => {
  // 支持从历史记录「复用」跳转带入数据
  const reused = sessionStorage.getItem('acp_reuse')
  if (reused) {
    sessionStorage.removeItem('acp_reuse')
    const data = JSON.parse(reused)
    result.value = data
    form.topic = data.topic || form.topic
    form.duration = data.duration || form.duration
    form.platform = data.platform || form.platform
    form.style = data.style || form.style
  }
  // 模板库「使用脚本模板」带入自定义风格
  const styleFromTpl = sessionStorage.getItem('acp_style')
  if (styleFromTpl) {
    sessionStorage.removeItem('acp_style')
    form.custom_style = styleFromTpl
    toast.info('已带入模板设定的风格要求，点击生成即可应用')
  }
})
</script>

<style scoped>
.head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; }
.head-right { display: flex; gap: 8px; }
.layout { display: grid; grid-template-columns: 300px 1fr; gap: 24px; align-items: start; }
@media (max-width: 960px) { .layout { grid-template-columns: 1fr; } }
.left { position: sticky; top: 68px; }
.a-label { display: block; font-size: var(--fs-small); font-weight: 600; margin-bottom: 8px; }
.durations { display: flex; gap: 8px; flex-wrap: wrap; }
.dur { padding: 7px 14px; border-radius: 10px; background: var(--c-bg); color: var(--c-gray); font-size: var(--fs-small); transition: all var(--t-base) var(--ease); }
.dur.on { background: var(--c-blue); color: #fff; font-weight: 600; }
.budget { display: flex; align-items: center; gap: 10px; }
.lg-block { width: 100%; }
.center { text-align: center; }
.gen-skeleton { display: grid; gap: 12px; }
.empty-card { background: var(--c-bg); border-radius: var(--radius-lg); }
.warn-box { background: rgba(255, 159, 10, 0.08); border-radius: var(--radius-md); padding: 10px 16px; margin-bottom: 16px; display: flex; gap: 10px; flex-wrap: wrap; }
.action-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; background: #fff; padding: 10px 14px; border-radius: var(--radius-md); box-shadow: var(--shadow-card); }
.action-bar .helper-text { font-size: 11px; }
.topic-chip {
  display: inline-flex; align-items: center; gap: 4px; max-width: 240px;
  background: var(--c-blue-soft); color: var(--c-blue); border-radius: var(--radius-pill);
  padding: 3px 12px; font-size: var(--fs-tiny); font-weight: 600;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.spacer { flex: 1; }
.sec-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.plain { background: var(--c-bg); border-radius: var(--radius-md); padding: 14px 16px; line-height: 1.8; }
.hook { background: var(--c-blue-soft); border-radius: var(--radius-md); padding: 14px 16px; color: var(--c-blue); font-weight: 600; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.hook-tag { font-size: 11px; background: #fff; padding: 2px 8px; border-radius: var(--radius-pill); color: var(--c-blue); }
.ml8 { margin-left: auto; }
.nowrap { white-space: nowrap; }
/* 表格自适应：横向滚动容器 + 各列最小宽度，避免标签竖排/内容挤压 */
.table-scroll { overflow-x: auto; border-radius: var(--radius-md); }
.scene { max-width: 200px; min-width: 140px; color: var(--c-gray); font-size: 13px; white-space: normal; }
.lines { min-width: 210px; }
.subtitle { color: var(--c-blue); font-weight: 500; min-width: 130px; }
.type-cell { white-space: nowrap; }
.title-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
@media (max-width: 760px) { .title-grid { grid-template-columns: 1fr; } }
.title-item { display: flex; align-items: center; gap: 10px; background: var(--c-bg); border-radius: 10px; padding: 10px 12px; }
.idx { width: 20px; color: var(--c-gray); font-size: var(--fs-tiny); flex-shrink: 0; }
.t-text { flex: 1; font-size: var(--fs-small); }
.tags-wrap { display: flex; flex-direction: column; gap: 12px; }
.tier-row { display: flex; align-items: flex-start; gap: 14px; }
.tier-label { flex-shrink: 0; width: 84px; font-size: var(--fs-tiny); color: var(--c-gray); padding-top: 4px; }
.tier-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tts-block { background: var(--c-bg); border-radius: var(--radius-md); padding: 18px 20px; }
.tts-block p { font-size: var(--fs-body); line-height: 2; margin-bottom: 4px; }
</style>
