<template>
  <div class="page">
    <h1 class="page-title">历史记录</h1>
    <p class="helper-text mt-8 mb-24">全部生成记录永久留存，支持检索、复用、二次导出与软删除恢复</p>

    <!-- 筛选栏 -->
    <ACard class="filter">
      <div class="toolbar">
        <div class="search">
          <svg width="15" height="15" viewBox="0 0 20 20"><circle cx="9" cy="9" r="6" stroke="#86868b" stroke-width="1.8" fill="none"/><path d="M13.5 13.5L17 17" stroke="#86868b" stroke-width="1.8" stroke-linecap="round"/></svg>
          <input v-model="keyword" placeholder="搜索主题或内容关键词" @keyup.enter="load(1)" />
        </div>
        <ASelect v-model="type" style="width:140px" :options="[{label:'全部类型',value:''},{label:'脚本',value:'script'},{label:'标题标签',value:'titles'},{label:'文案改写',value:'copywriting'}]" @update:model-value="load(1)" />
        <ASelect v-model="platform" style="width:140px" :options="[{label:'全部平台',value:''},{label:'抖音',value:'douyin'},{label:'小红书',value:'xiaohongshu'},{label:'视频号',value:'shipinhao'},{label:'哔哩哔哩',value:'bilibili'}]" @update:model-value="load(1)" />
        <AButton kind="secondary" @click="load(1)">筛选</AButton>
        <span class="spacer" />
        <span class="helper-text">共 {{ total }} 条</span>
      </div>
      <!-- 批量操作栏 -->
      <div v-if="selected.size" class="batch-bar">
        <span class="helper-text">已选 <b style="color:var(--c-blue)">{{ selected.size }}</b> 条</span>
        <AButton size="sm" kind="secondary" :loading="bulkBusy" @click="bulkExport">📦 打包导出 Word</AButton>
        <AButton size="sm" kind="danger" :loading="bulkBusy" @click="bulkDelete">🗑 批量移入回收站</AButton>
        <AButton size="sm" kind="ghost" @click="selected.clear()">取消选择</AButton>
      </div>
    </ACard>

    <!-- 卡片网格 -->
    <div v-if="loading" class="grid mt-24">
      <div v-for="i in 6" :key="i" class="skeleton" style="height:150px" />
    </div>

    <template v-else-if="records.length">
      <div class="grid mt-24">
        <ACard v-for="r in records" :key="r.id" hover class="rec"
          :class="{ selected: selected.has(r.id) }" @click="toggleSelect(r.id, $event)">
          <div class="rec-head">
            <input type="checkbox" class="cb" :checked="selected.has(r.id)" @click.stop="toggleSelect(r.id)" />
            <ATag :text="typeLabel(r.record_type)" />
            <ATag v-if="r.platform" :text="platLabel(r.platform)" tone="gray" />
            <span class="spacer" />
            <span class="helper-text">{{ r.created_at.slice(5, 16) }}</span>
          </div>
          <h3 class="rec-title">{{ r.topic }}</h3>
          <p class="helper-text rec-desc">{{ excerpt(r) }}</p>
          <div class="rec-foot" @click.stop>
            <AButton kind="ghost" size="sm" @click="view(r)">查看</AButton>
            <AButton v-if="r.record_type === 'script'" kind="ghost" size="sm" @click="reuse(r)">复用</AButton>
            <AButton kind="ghost" size="sm" @click="exportRec(r)">Word</AButton>
            <span class="spacer" />
            <AButton kind="danger" size="sm" @click="del(r)">删除</AButton>
          </div>
        </ACard>
      </div>
      <div class="mt-24">
        <APagination :total="total" :page="page" :page-size="size" @update:page="load" />
      </div>
    </template>

    <AEmpty v-else class="mt-24 empty" text="暂无记录" hint="去脚本生成页创作第一条内容吧" />

    <!-- 查看弹窗 -->
    <AModal v-model="showDetail" :title="detail?.topic || '记录详情'" width="720">
      <template v-if="detail">
        <div class="mb-16">
          <ATag :text="typeLabel(detail.record_type)" />
          <ATag v-if="detail.platform" :text="platLabel(detail.platform)" tone="gray" />
          <ATag v-if="detail.style" :text="detail.style" tone="gray" />
          <ATag :text="'模型：' + detail.source_model" tone="gray" />
        </div>
        <pre class="detail-pre">{{ detail.body_text || JSON.stringify(detail.content, null, 2) }}</pre>
        <div v-if="detail.tts_text" class="tts-box">
          <div class="sec-head mb-8">
            <h4 class="section-title" style="font-size:15px">TTS 配音文稿</h4>
            <span class="spacer" />
            <CopyBtn :text="detail.tts_text" />
          </div>
          <pre class="detail-pre">{{ detail.tts_text }}</pre>
        </div>
      </template>
      <template #footer>
        <AButton kind="secondary" @click="showDetail = false">关闭</AButton>
        <AButton @click="exportRec(detail)">导出 Word</AButton>
      </template>
    </AModal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import ACard from '../components/ui/ACard.vue'
import ASelect from '../components/ui/ASelect.vue'
import AButton from '../components/ui/AButton.vue'
import ATag from '../components/ui/ATag.vue'
import AEmpty from '../components/ui/AEmpty.vue'
import AModal from '../components/ui/AModal.vue'
import CopyBtn from '../components/ui/CopyBtn.vue'
import APagination from '../components/ui/APagination.vue'
import { api, downloadFile } from '../api/client'
import { toast } from '../stores/toast'
import { confirm } from '../stores/confirm'

const router = useRouter()
const records = ref([])
const total = ref(0)
const page = ref(1)
const size = 12
const keyword = ref('')
const type = ref('')
const platform = ref('')
const loading = ref(false)
const bulkBusy = ref(false)
const showDetail = ref(false)
const detail = ref(null)
const selected = reactive(new Set())

const typeLabel = t => ({ script: '短视频脚本', titles: '标题&标签', copywriting: '文案改写', tts: '配音文本' }[t] || t)
const platLabel = p => ({ douyin: '抖音', xiaohongshu: '小红书', shipinhao: '视频号', bilibili: 'B站' }[p] || p)
const maxPage = computed(() => Math.max(1, Math.ceil(total.value / size)))
const excerpt = (r) => {
  if (r.record_type === 'script') return `🎬 ${r.content?.hook || ''}`
  return (r.body_text || '').slice(0, 60)
}

const qs = () => {
  const p = new URLSearchParams()
  p.set('filter_keyword', keyword.value)
  p.set('grade', type.value)
  p.set('platform', platform.value)
  p.set('page', page.value); p.set('page_size', size)
  return '?' + p.toString()
}
const load = async (p = 1) => {
  page.value = p
  selected.clear()
  loading.value = true
  try {
    const data = await api.listHistory(qs())
    records.value = data.records
    total.value = data.total
  } finally { loading.value = false }
}
const toggleSelect = (id, ev) => {
  if (selected.has(id)) selected.delete(id)
  else selected.add(id)
  /* 触发响应式更新 */
  records.value = [...records.value]
}
const view = async (r) => { detail.value = r; showDetail.value = true }
const reuse = (r) => {
  const c = r.content || {}
  const bundle = {
    record_id: r.id, topic: r.topic, platform: r.platform, duration: r.duration,
    style: r.style, overview: c.topic_overview || '', hook: c.hook || '',
    segments: c.segments || [], ending: c.ending || '',
    titles: r.titles || [], title_items: c.titles || [],
    tags: r.tags || [], tts_text: r.tts_text || '', body_text: r.body_text || '',
    source_model: r.source_model, warnings: []
  }
  sessionStorage.setItem('acp_reuse', JSON.stringify(bundle))
  router.push('/script')
}
const del = async (r) => {
  const ok = await confirm({
    title: '删除记录',
    message: `「${r.topic}」将移入回收站（可恢复，数据安全无忧）。确定删除？`,
    danger: true, okText: '移入回收站'
  })
  if (!ok) return
  await api.deleteHistory(r.id)
  toast.info('已移入回收站（数据仍在，可通过记录接口恢复）')
  load(page.value)
}
const exportRec = async (r) => {
  const blob = await downloadFile(`/export/record/${r.id}`)
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${typeLabel(r.record_type)}_${r.topic.slice(0, 20)}.docx`
  a.click(); URL.revokeObjectURL(a.href)
  toast.success('Word 文档已导出')
}
const bulkExport = async () => {
  toast.info('文件生成中，请稍候，完成后自动下载…')
  const blob = await downloadFile('/history/bulk-export', {})
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'history_export.zip'
  a.click(); URL.revokeObjectURL(a.href)
  toast.success('全部选中记录已打包导出')
}
const bulkDelete = async () => {
  const ok = await confirm({
    title: '批量删除',
    message: `将 ${selected.size} 条记录移入回收站（可恢复）。确定？`,
    danger: true, okText: '批量移入回收站'
  })
  if (!ok) return
  bulkBusy.value = true
  try {
    await api.bulkDeleteHistory([...selected])
    toast.success(`${selected.size} 条记录已批量移入回收站`)
    load(page.value)
  } finally { bulkBusy.value = false }
}

onMounted(() => load(1))
</script>

<style scoped>
.filter { padding: 16px 20px; }
.search { display: flex; align-items: center; gap: 8px; background: var(--c-bg); border-radius: var(--radius-md); padding: 0 14px; height: 40px; width: 250px; }
.search input { border: none; outline: none; background: transparent; flex: 1; font-size: var(--fs-body); }
.spacer { flex: 1; }
.batch-bar {
  display: flex; align-items: center; gap: 12px; margin-top: 12px; padding-top: 12px;
  border-top: 1px solid var(--c-line); flex-wrap: wrap;
}
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 900px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
.rec { display: flex; flex-direction: column; padding: 18px 20px; cursor: pointer; }
.rec.selected { outline: 2px solid var(--c-blue); }
.cb { width: 16px; height: 16px; accent-color: var(--c-blue); cursor: pointer; }
.rec-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.rec-title { font-size: 15px; margin: 12px 0 6px; line-height: 1.5; }
.rec-desc { line-height: 1.6; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.rec-foot { display: flex; align-items: center; gap: 2px; margin-top: auto; padding-top: 12px; }
.pager { display: flex; align-items: center; justify-content: center; gap: 16px; }
.empty { background: var(--c-bg); border-radius: var(--radius-lg); }
.detail-pre { white-space: pre-wrap; background: var(--c-bg); border-radius: var(--radius-md); padding: 16px; font-size: var(--fs-small); line-height: 1.8; font-family: inherit; }
.tts-box { margin-top: 16px; }
.sec-head { display: flex; align-items: center; gap: 12px; }
</style>
