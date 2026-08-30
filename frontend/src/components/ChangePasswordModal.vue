<template>
  <AModal :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)"
    title="修改密码" width="420">
    <AInput v-model="oldPwd" label="原密码" type="password" />
    <div class="mt-16">
      <AInput v-model="newPwd" label="新密码（至少 6 位）" type="password" />
    </div>
    <div class="mt-16">
      <AInput v-model="newPwd2" label="确认新密码" type="password" />
    </div>
    <template #footer>
      <AButton kind="secondary" @click="$emit('update:modelValue', false)">取消</AButton>
      <AButton :loading="saving" :disabled="!newPwd" @click="save">确认修改</AButton>
    </template>
  </AModal>
</template>

<script setup>
import { ref } from 'vue'
import AModal from './ui/AModal.vue'
import AInput from './ui/AInput.vue'
import AButton from './ui/AButton.vue'
import { api } from '../api/client'
import { toast } from '../stores/toast'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue'])
const oldPwd = ref('')
const newPwd = ref('')
const newPwd2 = ref('')
const saving = ref(false)

const save = async () => {
  if (newPwd.value !== newPwd2.value) return toast.error('两次输入的新密码不一致')
  if (newPwd.value.length < 6) return toast.error('新密码至少 6 位')
  saving.value = true
  try {
    await api.changePassword({ old_password: oldPwd.value, new_password: newPwd.value })
    toast.success('密码修改成功，下次登录请使用新密码')
    emit('update:modelValue', false)
  } finally { saving.value = false }
}
</script>
