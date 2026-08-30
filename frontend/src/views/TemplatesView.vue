<template>
  <div class="page">
    <h1 class="page-title">自定义模板库</h1>
    <p class="helper-text mt-8 mb-24">脚本模板 / 文案风格模板 / Prompt 模板：命名分类、一键复用、随时编辑</p>

    <div class="toolbar mb-24">
      <ATabs v-model="scene" :tabs="[{label:'脚本模板',value:'script'},{label:'风格模板',value:'style'},{label:'Prompt 模板',value:'prompt'}]" />
      <AInput v-model="keyword" placeholder="搜索模板名称/描述" class="kw" @keyup.enter="page = 1; load()" />
      <AButton kind="secondary" @click="page = 1; load()">搜索</AButton>
      <span class="spacer" />
      <span class="helper-text">共 {{ total }} 个模板</span>
      <AButton @click="openCreate">+ 新建模板</AButton>
    </div>

    <div v-if="list.length" class="grid">
      <ACard v-for="t in list" :key="t.id" hover class="tpl">
        <div class="tpl-head">
          <h3 class="tpl-name">{{ t.name }}</h3>
          <span class="helper-text">{{ t.updated_at.slice(5, 16) }}</span>
        </div>
        <p class="helper-text tpl-desc">{{ t.description || '暂无描述' }}</p>
        <div class="tpl-body">{{ t.content }}</div>
        <div class="tpl-foot">
          <AButton kind="ghost" size="sm" @click="useTpl(t)">▶ 使用模板</AButton>
          <AButton kind="ghost" size="sm" @click="openEdit(t)">编辑</AButton>
          <AButton kind="ghost" size="sm" @click="copyContent(t)">复制内容</AButton>
          <span class="spacer" />
          <AButton kind="danger" size="sm" @click="remove(t)">删除</AButton>
        </div>
      </ACard>
    </div>
    <div v-if="list.length" class="mt-16">
      <APagination :total="total" :page="page" :page-size="pageSize" @update:page="onPage" />
    </div>
    <AEmpty v-else class="mt-24 empty" text="该分类还没有模板" hint="沉淀你的高频模板，提升重复创作效率" />

    <AModal v-model="showModal" :title="editing ? '编辑模板' : '新建模板'" width="620">
      <div class="form-grid">
        <AInput v-model="form.name" label="模板名称" placeholder="例如：知识口播万能框架" />
        <ASelect v-model="form.scene_type" label="场景类型" :options="sceneOptions" />
      </div>
      <div class="mt-16">
        <AInput v-model="form.description" label="描述（可选）" placeholder="一句话说明模板用途" />
      </div>
      <div class="mt-16">
        <ATextarea v-model="form.content" label="模板内容" :rows="8" count :maxlength="20000"
          placeholder="模板正文 / Prompt 内容，支持 {主题} {平台} {时长} 占位符" />
      </div>
      <template #footer>
        <AButton kind="secondary" @click="showModal = false">取消</AButton>
        <AButton :loading="saving" @click="save">保存</AButton>
      </template>
    </AModal>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import ACard from '../components/ui/ACard.vue'
import AInput from '../components/ui/AInput.vue'
import ATextarea from '../components/ui/ATextarea.vue'
import ASelect from '../components/ui/ASelect.vue'
import AButton from '../components/ui/AButton.vue'
import ATabs from '../components/ui/ATabs.vue'
import AEmpty from '../components/ui/AEmpty.vue'
import AModal from '../components/ui/AModal.vue'
import APagination from '../components/ui/APagination.vue'
import { api } from '../api/client'
import { toast } from '../stores/toast'
import { confirm } from '../stores/confirm'

const router = useRouter()
const scene = ref('script')
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const keyword = ref('')
const showModal = ref(false)
const editing = ref(null)
const saving = ref(false)
const form = reactive({ name: '', scene_type: 'script', content: '', description: '' })

const sceneOptions = [
  { label: '脚本模板', value: 'script' },
  { label: '风格模板', value: 'style' },
  { label: 'Prompt 模板', value: 'prompt' }
]

const load = async () => {
  const p = new URLSearchParams()
  p.set('grade', scene.value)
  p.set('page', page.value); p.set('page_size', pageSize)
  if (keyword.value) p.set('filter_keyword', keyword.value)
  const data = await api.listTemplates('?' + p.toString())
  list.value = data.records
  total.value = data.total
  if (page.value > 1 && !data.records.length) { page.value = 1; load() }  // 越界自动回第 1 页
}
const onPage = (p) => { page.value = p; load() }
watch(scene, () => { page.value = 1; load() })   // 切换分级筛选 → 重置页码回第 1 页

const openCreate = () => {
  editing.value = null
  Object.assign(form, { name: '', scene_type: scene.value, content: '', description: '' })
  showModal.value = true
}
const openEdit = (t) => {
  editing.value = t
  Object.assign(form, { name: t.name, scene_type: t.scene_type, content: t.content, description: t.description })
  showModal.value = true
}
const save = async () => {
  if (!form.name.trim()) return toast.error('请填写模板名称')
  if (form.content.trim().length < 5) return toast.error('模板内容至少 5 字')
  saving.value = true
  try {
    if (editing.value) await api.updateTemplate(editing.value.id, { ...form })
    else await api.createTemplate({ ...form })
    toast.success('模板已保存')
    showModal.value = false
    load()
  } finally { saving.value = false }
}
const remove = async (t) => {
  const ok = await confirm({
    title: '删除模板',
    message: `模板「${t.name}」将被永久删除。确定？`,
    danger: true, okText: '删除'
  })
  if (!ok) return
  await api.deleteTemplate(t.id)
  toast.info('模板已删除')
  load()
}
const copyContent = async (t) => {
  await navigator.clipboard.writeText(t.content)
  toast.success('模板内容已复制')
}

/** 使用模板：脚本/Prompt 模板 → 带入脚本页自定义风格；风格模板 → 带入改写页 */
const useTpl = (t) => {
  if (t.scene_type === 'style') {
    sessionStorage.setItem('acp_copy_style', t.content.slice(0, 200))
    router.push('/copywriting')
    toast.success('风格模板已带入「文案改写」页的自定义风格，粘贴原文即可应用')
    return
  }
  sessionStorage.setItem('acp_style', t.content.slice(0, 200))
  router.push('/script')
  toast.success('模板已带入「脚本生成」页的自定义风格要求，输入主题即可应用')
}

onMounted(load)
</script>

<style scoped>
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; align-items: start; }
@media (max-width: 900px) { .grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
.tpl { display: flex; flex-direction: column; padding: 20px; min-height: 210px; }
.tpl-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.tpl-name { font-size: 15px; }
.tpl-desc { margin: 6px 0 10px; }
.tpl-body {
  font-size: var(--fs-small); color: var(--c-gray); line-height: 1.7;
  background: var(--c-bg); border-radius: var(--radius-sm); padding: 10px 12px;
  flex: 1; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical;
}
.tpl-foot { display: flex; align-items: center; gap: 2px; padding-top: 12px; flex-wrap: wrap; }
.spacer { flex: 1; }
.empty { background: var(--c-bg); border-radius: var(--radius-lg); }
.form-grid { display: grid; grid-template-columns: 1fr 200px; gap: 12px; }
.kw { width: 240px; }
</style>
