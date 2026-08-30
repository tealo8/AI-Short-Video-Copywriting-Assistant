<template>
  <div class="page">
    <h1 class="page-title">批量内容生成</h1>
    <p class="helper-text mt-8 mb-24">TXT / CSV / Excel 导入主题清单，后台异步量产「脚本+标题+标签+配音稿」全套内容</p>

    <div class="create-row">
      <!-- 上传区 -->
      <ACard class="upload-card" :class="{ drag: dragging }"
        @dragover.prevent="dragging = true" @dragleave="dragging = false" @drop.prevent="onDrop">
        <input ref="fileInput" type="file" accept=".txt,.csv,.xlsx" hidden @change="onFile" />
        <div class="upload-zone" @click="fileInput.click()">
          <div class="u-icon">⤒</div>
          <p class="u-main">拖拽文件到这里，或点击选择</p>
          <p class="helper-text">支持 .txt / .csv / .xlsx · 每行一个主题 · 最多 50 条</p>
          <a class="tpl-link" @click.stop="downloadTemplate">⬇ 下载导入模板（示例格式）</a>
        </div>
        <div v-if="uploadError" class="upload-error">
          {{ uploadError }}
        </div>
      </ACard>

      <!-- 配置 -->
      <ACard class="config-card">
        <div class="grid2">
          <ASelect v-model="platform" label="平台" :options="platforms" />
          <ASelect v-model="style" label="风格" :options="styles" />
        </div>
        <div class="mt-16">
          <label class="a-label">视频时长</label>
          <div class="durations">
            <button v-for="d in durations" :key="d" class="dur" :class="{ on: duration === d }"
              @click="duration = d">{{ d }}s</button>
          </div>
        </div>
        <div class="mt-16">
          <label class="a-label">或直接输入主题（每行一条）</label>
          <textarea v-model="topicsText" class="topics" rows="4"
            :placeholder="textareaPlaceholder"
            @input="checkLimit" />
          <p class="helper-text mt-8" :class="{ 'limit-hit': topicCount >= 50 }">
            已输入 {{ topicCount }} 条 / 上限 50 条
            <template v-if="topicCount >= 50">（已达上限，请分批提交）</template>
          </p>
        </div>
        <AButton class="mt-16 lg-block" size="lg" :loading="creating"
          :disabled="topicCount >= 50" @click="createByText">
          🚀 创建批量任务{{ topicCount >= 50 ? '（已达上限）' : '' }}
        </AButton>
        <p class="helper-text mt-8" v-if="runningCount >= maxConcurrent">
          当前已有 {{ runningCount }} 个任务在并行生成（上限 {{ maxConcurrent }}），新任务将排队等待
        </p>
      </ACard>
    </div>

    <!-- 任务列表 -->
    <div class="list-head mt-48">
      <h2 class="section-title mb-16">任务列表</h2>
      <div class="toolbar">
        <AInput v-model="taskKeyword" placeholder="按任务名称搜索" class="task-kw" @keyup.enter="tasksPage = 1; refresh()" />
        <ASelect v-model="taskStatus" style="width:150px" :options="[
          {label:'全部状态',value:''},{label:'排队中',value:'pending'},{label:'生成中',value:'running'},
          {label:'已完成',value:'completed'},{label:'部分失败',value:'partial'},{label:'全部失败',value:'failed'},{label:'已取消',value:'cancelled'}
        ]" @update:model-value="tasksPage = 1; refresh()" />
        <AButton kind="secondary" @click="tasksPage = 1; refresh()">刷新</AButton>
      </div>
    </div>
    <div v-if="tasks.length" class="task-list">
      <ACard v-for="t in tasks" :key="t.id" class="task-item">
        <div class="task-head">
          <div class="task-meta">
            <span class="task-id">#{{ t.id }}</span>
            <span class="task-name">{{ t.name }}</span>
            <span class="task-time helper-text">{{ t.created_at }}</span>
          </div>
          <div class="task-actions">
            <ATag :text="statusLabel(t.status)" :tone="statusTone(t.status)" />
            <AButton kind="secondary" size="sm" @click="viewDetail(t)">查看结果</AButton>
            <AButton v-if="t.failed > 0 && isTerminal(t)" kind="secondary" size="sm" @click="retry(t)">重试失败</AButton>
            <AButton v-if="isTerminal(t)" kind="secondary" size="sm" @click="downloadExcel(t)">下载 Excel</AButton>
            <AButton v-if="isTerminal(t)" kind="secondary" size="sm" @click="downloadWord(t)">下载 Word</AButton>
            <AButton v-if="t.status === 'running'" kind="secondary" size="sm" @click="cancel(t)">终止</AButton>
            <AButton kind="danger" size="sm" @click="remove(t)">删除</AButton>
          </div>
        </div>
        <div class="mt-16">
          <AProgress :value="t.progress" />
        </div>
        <div class="stats helper-text mt-8">
          共 <b>{{ t.total }}</b> 条 · 成功 <b style="color:#248a3d">{{ t.success }}</b> ·
          失败 <b style="color:#d70015">{{ t.failed }}</b> ·
          耗时 {{ t.duration ? t.duration + 's' : '—' }} ·
          排队状态 {{ queueLabel(t) }}
        </div>
      </ACard>
      <div class="mt-16">
        <APagination :total="tasksTotal" :page="tasksPage" :page-size="10" @update:page="onTasksPage" />
      </div>
    </div>
    <AEmpty v-else class="mt-24 empty" text="还没有批量任务" hint="导入主题清单或直接粘贴，一键开始量产" />

    <!-- 结果详情弹窗 -->
    <AModal v-model="showDetail" :title="`任务 #${detail?.id} ${detail?.name || ''}`" width="720">
      <template v-if="detail">
        <div class="detail-stats mb-16">
          <ATag :text="statusLabel(detail.status)" :tone="statusTone(detail.status)" />
          <ATag :text="`成功 ${detail.success}`" tone="green" />
          <ATag :text="`失败 ${detail.failed}`" tone="red" />
          <ATag :text="`总 ${detail.total}`" tone="gray" />
          <template v-if="detail.meta">
            <ATag :text="platLabel(detail.meta.platform)" tone="gray" />
            <ATag :text="`${detail.meta.duration}s`" tone="gray" />
            <ATag :text="detail.meta.style" tone="gray" />
          </template>
        </div>
        <div class="detail-list">
          <div v-for="item in detail.items" :key="item.index" class="detail-row" :class="{ 'is-failed': item.status === 'failed' }">
            <span class="i-idx">#{{ item.index }}</span>
            <div class="i-main">
              <div class="i-topic">{{ item.topic }}</div>
              <div v-if="item.error" class="i-error helper-text">{{ item.error }}</div>
              <div v-if="item.status === 'success'" class="i-error helper-text" style="color:#248a3d">
                已生成（记录 #{{ item.result_id }}，模型 {{ item.source_model }}）
              </div>
            </div>
            <ATag :text="itemLabel(item.status)" :tone="itemTone(item.status)" />
            <CopyBtn v-if="item.status === 'success'" :text="`#${item.index} ${item.topic}`" />
          </div>
        </div>
      </template>
    </AModal>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import ACard from '../components/ui/ACard.vue'
import ASelect from '../components/ui/ASelect.vue'
import AButton from '../components/ui/AButton.vue'
import AProgress from '../components/ui/AProgress.vue'
import ATag from '../components/ui/ATag.vue'
import AModal from '../components/ui/AModal.vue'
import AEmpty from '../components/ui/AEmpty.vue'
import CopyBtn from '../components/ui/CopyBtn.vue'
import AInput from '../components/ui/AInput.vue'
import APagination from '../components/ui/APagination.vue'
import { api, downloadFile } from '../api/client'
import { toast } from '../stores/toast'
import { confirm } from '../stores/confirm'

const fileInput = ref(null)
const dragging = ref(false)
const platform = ref('douyin')
const style = ref('通用')
const duration = ref(60)
const topicsText = ref('')
const creating = ref(false)
const uploadError = ref('')
const tasks = ref([])
const tasksTotal = ref(0)
const tasksPage = ref(1)
const taskKeyword = ref('')
const taskStatus = ref('')
const showDetail = ref(false)
const detail = ref(null)
const downloading = ref(false)
const maxConcurrent = 2
let pollTimer = null

const platforms = [
  { label: '抖音', value: 'douyin' }, { label: '小红书', value: 'xiaohongshu' },
  { label: '视频号', value: 'shipinhao' }, { label: '哔哩哔哩', value: 'bilibili' }
]
const styles = [
  { label: '通用', value: '通用' }, { label: '小红书温柔种草风', value: '小红书温柔种草风' },
  { label: '抖音口播干货风', value: '抖音口播干货风' }, { label: '正式专业科普风', value: '正式专业科普风' },
  { label: '幽默轻松段子风', value: '幽默轻松段子风' }, { label: '电商带货营销风', value: '电商带货营销风' },
  { label: '极简高级短句风', value: '极简高级短句风' }
]
const durations = [30, 60, 90, 120, 180]

const topicCount = computed(() => topicsText.value.split('\n').map(s => s.trim()).filter(Boolean).length)
const runningCount = computed(() => tasks.value.filter(t => t.status === 'running' || t.status === 'pending').length)
const textareaPlaceholder = 'AI 副业入门\n小红书涨粉技巧\n普通人拍vlog'
const checkLimit = () => {
  if (topicCount.value >= 50) toast.info('已达单次任务上限 50 条，请分批提交')
}

const statusLabel = s => ({ pending: '排队中', running: '生成中', completed: '已完成', partial: '部分失败', failed: '全部失败', cancelled: '已取消' }[s] || s)
const statusTone = s => ({ running: 'blue', completed: 'green', partial: 'amber', failed: 'red', cancelled: 'gray', pending: 'amber' }[s] || 'gray')
const itemLabel = s => ({ pending: '等待', success: '成功', failed: '失败', cancelled: '取消' }[s] || s)
const itemTone = s => ({ success: 'green', failed: 'red', cancelled: 'gray', pending: 'gray' }[s] || 'gray')
const platLabel = p => ({ douyin: '抖音', xiaohongshu: '小红书', shipinhao: '视频号', bilibili: 'B站' }[p] || p)
const isTerminal = t => ['completed', 'partial', 'failed', 'cancelled'].includes(t.status)
const queueLabel = (t) => t.status === 'pending' ? `第 ${runningCount.value} 个排队，等待空余并发` : '—'

const poll = async () => {
  try {
    const p = new URLSearchParams()
    p.set('page', tasksPage.value); p.set('page_size', 10)
    if (taskKeyword.value) p.set('filter_keyword', taskKeyword.value)
    if (taskStatus.value) p.set('grade', taskStatus.value)
    const data = await api.listBatch('?' + p.toString())
    tasks.value = data.records
    tasksTotal.value = data.total
  } catch { /* 静默 */ }
}
const refresh = poll
const onTasksPage = (p) => { tasksPage.value = p; refresh() }

const createByText = async () => {
  const topics = topicsText.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (!topics.length) return toast.error('请粘贴主题或上传文件')
  if (topics.length > 50) return toast.error('单次最多 50 条，请分批提交')
  if (runningCount.value >= maxConcurrent) toast.info('当前并发已满，新任务已加入排队')
  creating.value = true
  try {
    await api.createBatch({ name: `批量任务 ${new Date().toLocaleString()}`, topics, platform: platform.value, duration: duration.value, style: style.value })
    toast.success('批量任务已创建，后台生成中')
    topicsText.value = ''
    refresh()
  } finally { creating.value = false }
}

const startUpload = async (file) => {
  uploadError.value = ''
  creating.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('platform', platform.value)
    form.append('duration', String(duration.value))
    form.append('style', style.value)
    const data = await api.uploadBatch(form)
    toast.success(`已导入 ${data.count} 条主题，任务 #${data.task_id} 开始生成`)
    refresh()
  } catch (e) {
    uploadError.value = `文件解析失败：${e.message}（支持每行一个主题的 .txt / .csv / .xlsx，可先下载模板对比格式）`
  } finally { creating.value = false }
}
const onFile = (e) => { if (e.target.files[0]) startUpload(e.target.files[0]) }
const onDrop = (e) => { dragging.value = false; if (e.dataTransfer.files[0]) startUpload(e.dataTransfer.files[0]) }

const downloadTemplate = async () => {
  const blob = await downloadFile('/batch/template')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = 'batch_template.txt'; a.click()
  URL.revokeObjectURL(a.href)
  toast.success('模板已下载：每行一个主题，可在此文件内直接编辑')
}

const saveBlob = (blob, name) => {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = name; a.click()
  URL.revokeObjectURL(a.href)
}

const downloadExcel = async (t) => {
  const blob = await downloadFile(`/batch/tasks/${t.id}/download`)
  saveBlob(blob, `batch_result_${t.id}.xlsx`)
  toast.success('结果表格已导出')
}

const downloadWord = async (t) => {
  toast.info('文件生成中，请稍候，完成后自动下载…')
  try {
    const blob = await downloadFile(`/batch/tasks/${t.id}/download-docx`)
    saveBlob(blob, `batch_docx_${t.id}.zip`)
    toast.success('全部 Word 文档已打包下载')
  } catch { /* toast 已提示 */ }
}

const viewDetail = async (t) => {
  detail.value = await api.batchDetail(t.id)
  showDetail.value = true
}

const cancel = async (t) => {
  const ok = await confirm({
    title: '终止批量任务',
    message: `任务 #${t.id} 正在生成中，终止后将跳过剩余条目。确定终止？`,
    danger: true, okText: '终止任务'
  })
  if (!ok) return
  await api.cancelBatch(t.id)
  toast.info('已请求终止，剩余条目将跳过')
  refresh()
}

const retry = async (t) => {
  const ok = await confirm({
    title: '重试失败条目',
    message: `将重新排队生成任务 #${t.id} 的 ${t.failed} 条失败条目，已成功的条目不受影响。确定？`,
    okText: '开始重试'
  })
  if (!ok) return
  try {
    const data = await api.retryBatch(t.id)
    toast.success(`${data.retried} 条失败条目已重新排队`)
    refresh()
  } catch { /* toast 已提示 */ }
}

const remove = async (t) => {
  const ok = await confirm({
    title: '删除任务记录',
    message: `删除后无法恢复（生成的记录仍保留在历史记录中）。确定删除任务 #${t.id}？`,
    danger: true, okText: '删除'
  })
  if (!ok) return
  await api.del(`/batch/tasks/${t.id}`)
  toast.info('任务记录已删除')
  refresh()
}

onMounted(() => { poll(); pollTimer = setInterval(poll, 3000) })
onBeforeUnmount(() => clearInterval(pollTimer))
</script>

<style scoped>
.create-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 880px) { .create-row { grid-template-columns: 1fr; } }
.upload-card { border: 1.5px dashed var(--c-gray-light); background: #fff; box-shadow: none; transition: all var(--t-base) var(--ease); }
.upload-card.drag { border-color: var(--c-blue); background: var(--c-blue-soft); }
.upload-zone { min-height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; text-align: center; gap: 8px; }
.u-icon { font-size: 30px; width: 56px; height: 56px; border-radius: 50%; background: var(--c-bg); display: flex; align-items: center; justify-content: center; color: var(--c-blue); }
.u-main { font-weight: 500; }
.tpl-link { color: var(--c-blue); font-size: var(--fs-tiny); cursor: pointer; }
.tpl-link:hover { text-decoration: underline; }
.upload-error { background: rgba(255, 59, 48, 0.08); color: #d70015; border-radius: var(--radius-md); padding: 10px 14px; font-size: var(--fs-tiny); margin: 0 14px 14px; line-height: 1.7; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.a-label { display: block; font-size: var(--fs-small); font-weight: 600; margin-bottom: 8px; }
.durations { display: flex; gap: 8px; flex-wrap: wrap; }
.dur { padding: 6px 13px; border-radius: 10px; background: var(--c-bg); color: var(--c-gray); font-size: var(--fs-tiny); transition: all var(--t-base) var(--ease); }
.dur.on { background: var(--c-blue); color: #fff; }
.topics { width: 100%; border: none; outline: none; background: var(--c-bg); border-radius: var(--radius-md); padding: 12px 14px; font-size: var(--fs-small); line-height: 1.7; resize: vertical; }
.topics:focus { box-shadow: 0 0 0 3px var(--c-blue-soft); }
.limit-hit { color: var(--c-amber); font-weight: 600; }
.lg-block { width: 100%; }
.task-list { display: flex; flex-direction: column; gap: 14px; }
.task-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.task-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.task-id { background: var(--c-blue-soft); color: var(--c-blue); font-weight: 700; padding: 3px 10px; border-radius: var(--radius-pill); font-size: var(--fs-tiny); }
.task-name { font-weight: 600; }
.task-actions { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.stats { display: flex; gap: 16px; flex-wrap: wrap; }
.empty { background: var(--c-bg); border-radius: var(--radius-lg); }
.list-head .toolbar { margin-bottom: 16px; }
.task-kw { width: 240px; }
.detail-stats { display: flex; gap: 8px; flex-wrap: wrap; }
.detail-list { max-height: 46vh; overflow: auto; }
.detail-row { display: flex; align-items: flex-start; gap: 12px; padding: 10px 4px; border-bottom: 1px solid var(--c-line); font-size: var(--fs-small); }
.detail-row.is-failed { background: rgba(255, 59, 48, 0.04); }
.i-idx { color: var(--c-gray); width: 34px; flex-shrink: 0; padding-top: 2px; }
.i-main { flex: 1; }
.i-error { margin-top: 4px; word-break: break-all; }
</style>
