<template>
  <AModal :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)"
    title="保存为模板" width="460">
    <AInput v-model="name" label="模板名称" placeholder="例如：知识口播万能框架（30s）" />
    <div class="mt-16">
      <ASelect v-model="scene" label="场景类型" :options="scenes" />
    </div>
    <div class="mt-16">
      <ATextarea v-model="description" label="描述（可选）" :rows="2" placeholder="一句话说明模板用途" />
    </div>
    <template #footer>
      <AButton kind="secondary" @click="$emit('update:modelValue', false)">取消</AButton>
      <AButton :loading="saving" @click="save">保存到模板库</AButton>
    </template>
  </AModal>
</template>

<script setup>
import { ref, watch } from 'vue'
import AModal from './ui/AModal.vue'
import AInput from './ui/AInput.vue'
import ATextarea from './ui/ATextarea.vue'
import ASelect from './ui/ASelect.vue'
import AButton from './ui/AButton.vue'
import { api } from '../api/client'
import { toast } from '../stores/toast'

const props = defineProps({
  modelValue: Boolean,
  defaultName: { type: String, default: '' },
  defaultScene: { type: String, default: 'script' },
  // 生成内容文本（脚本模板存套装正文 / 风格模板存风格摘要）
  content: { type: String, default: '' },
  defaultDescription: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue', 'saved'])
const scenes = [
  { label: '脚本模板', value: 'script' },
  { label: '风格模板', value: 'style' },
  { label: 'Prompt 模板', value: 'prompt' }
]
const name = ref('')
const scene = ref('script')
const description = ref('')
const saving = ref(false)

watch(() => props.modelValue, (v) => {
  if (v) {
    name.value = props.defaultName
    scene.value = props.defaultScene
    description.value = props.defaultDescription
  }
})

const save = async () => {
  if (!name.value.trim()) return toast.error('请填写模板名称')
  if (props.content.trim().length < 5) return toast.error('保存内容为空，请先生成内容')
  saving.value = true
  try {
    await api.createTemplate({
      name: name.value.trim(), scene_type: scene.value,
      description: description.value, content: props.content
    })
    toast.success('已保存到模板库，可在「模板库」页复用')
    emit('update:modelValue', false)
    emit('saved')
  } finally { saving.value = false }
}
</script>
