<template>
  <AModal :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)"
    title="模型配置" width="640">
    <div v-if="loading" class="skeleton" style="height: 260px" />
    <template v-else-if="cfg">
      <!-- Provider 优先级链 -->
      <label class="a-label">推理链（顺序即降级顺序，可点击开关）</label>
      <div class="chain">
        <div v-for="p in ['ollama', 'cloud', 'mock']" :key="p" class="chip"
          :class="{ on: chainOn(p) }" @click="toggleChain(p)">
          {{ name(p) }} ✓
        </div>
      </div>

      <!-- Ollama -->
      <div class="grid2 mt-16">
        <AInput v-model="cfg.OLLAMA_BASE_URL" label="Ollama 地址" placeholder="http://localhost:11434" />
        <AInput v-model="cfg.OLLAMA_MODEL" label="本地模型名" placeholder="qwen2.5:7b" />
      </div>

      <!-- 云端 -->
      <div class="grid2 mt-16">
        <AInput v-model="cfg.CLOUD_BASE_URL" label="云端接口地址（OpenAI 兼容）" placeholder="https://api.deepseek.com" />
        <AInput v-model="cfg.CLOUD_MODEL" label="云端模型名" placeholder="deepseek-chat" />
      </div>
      <div class="mt-16">
        <AInput v-model="cfg.CLOUD_API_KEY" label="云端 API Key" type="password" placeholder="sk-..."
          hint="已配置则显示脱敏值；修改后立即生效，无需重启" />
      </div>

      <!-- 生成参数 -->
      <div class="grid3 mt-16">
        <AInput v-model.number="cfg.LLM_TEMPERATURE" label="温度 (0-2)" type="number" />
        <AInput v-model.number="cfg.LLM_MAX_TOKENS" label="Token 上限" type="number" />
        <AInput v-model.number="cfg.LLM_TIMEOUT" label="超时（秒）" type="number" />
      </div>
      <div class="grid3 mt-16">
        <AInput v-model.number="cfg.LLM_RETRIES" label="重试次数" type="number" />
        <AInput v-model.number="cfg.BATCH_MAX_WORKERS" label="批量并发数" type="number" />
        <AInput v-model.number="cfg.BATCH_ITEM_LIMIT" label="批量条目上限" type="number" />
      </div>
    </template>

    <template #footer>
      <AButton kind="secondary" @click="$emit('update:modelValue', false)">取消</AButton>
      <AButton :loading="saving" @click="save">保存并立即生效</AButton>
    </template>
  </AModal>
</template>

<script setup>
import { ref, watch } from 'vue'
import AModal from './ui/AModal.vue'
import AInput from './ui/AInput.vue'
import AButton from './ui/AButton.vue'
import { api } from '../api/client'
import { useAuth } from '../stores/auth'
import { toast } from '../stores/toast'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue'])
const auth = useAuth()
const loading = ref(false)
const saving = ref(false)
const cfg = ref(null)

const name = (p) => ({ ollama: '本地 Ollama', cloud: '云端 API', mock: '演示兜底' }[p] || p)
const chainOn = (p) => (cfg.value?.LLM_PROVIDER_PRIORITY || '').split(',').includes(p)
const toggleChain = (p) => {
  const arr = (cfg.value.LLM_PROVIDER_PRIORITY || '').split(',').filter(Boolean)
  const i = arr.indexOf(p)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(p)
  // 保持语义顺序：ollama -> cloud -> mock
  const order = ['ollama', 'cloud', 'mock']
  cfg.value.LLM_PROVIDER_PRIORITY = order.filter(x => arr.includes(x)).join(',')
}

watch(() => props.modelValue, async (v) => {
  if (!v) return
  loading.value = true
  try { cfg.value = await api.systemConfig() } finally { loading.value = false }
})

const save = async () => {
  saving.value = true
  try {
    const payload = { ...cfg.value }
    delete payload._editable
    const data = await api.updateSystemConfig(payload)
    toast.success(`配置已更新并生效（${data.applied.length} 项）`)
    emit('update:modelValue', false)
    auth.refreshStatus()
  } finally { saving.value = false }
}
</script>

<style scoped>
.a-label { display: block; font-size: var(--fs-small); font-weight: 600; margin-bottom: 8px; }
.chain { display: flex; gap: 8px; flex-wrap: wrap; }
.chip {
  padding: 6px 14px; border-radius: var(--radius-pill); background: var(--c-bg);
  color: var(--c-gray); font-size: var(--fs-small); cursor: pointer; user-select: none;
  border: 1px solid transparent; transition: all var(--t-base) var(--ease);
}
.chip.on { background: var(--c-blue-soft); color: var(--c-blue); border-color: rgba(0, 113, 227, 0.3); font-weight: 600; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
</style>
