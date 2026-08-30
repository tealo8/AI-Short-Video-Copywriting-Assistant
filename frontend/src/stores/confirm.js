/* 全局确认弹窗（Promise API）：高危操作二次确认。
   用法：const ok = await confirm({ title:'删除记录', message:'删除后可在回收站恢复，确定？', danger:true }) */
import { reactive } from 'vue'

export const confirmState = reactive({
  visible: false,
  title: '确认操作',
  message: '',
  danger: false,
  okText: '确定',
  cancelText: '取消',
  resolve: null
})

export function confirm({ title = '确认操作', message = '', danger = false, okText = '确定', cancelText = '取消' } = {}) {
  return new Promise((resolve) => {
    Object.assign(confirmState, { visible: true, title, message, danger, okText, cancelText, resolve })
  })
}

export function resolveConfirm(ok) {
  confirmState.visible = false
  const fn = confirmState.resolve
  confirmState.resolve = null
  if (fn) fn(ok)
}
