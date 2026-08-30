<template>
  <AButton :kind="copied ? 'success' : 'ghost'" size="sm" @click="copy">
    {{ copied ? '已复制 ✓' : '复制' }}
  </AButton>
</template>

<script setup>
import { ref } from 'vue'
import AButton from './AButton.vue'
import { toast } from '../../stores/toast'

const props = defineProps({ text: { type: String, default: '' } })
const copied = ref(false)
const copy = async () => {
  try {
    await navigator.clipboard.writeText(props.text || '')
    copied.value = true
    toast.success('已复制到剪贴板')
    setTimeout(() => { copied.value = false }, 1600)
  } catch {
    toast.error('复制失败，请手动选择复制')
  }
}
</script>
