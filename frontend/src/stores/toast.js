/* Toast 全局轻提示：Apple 式轻柔反馈，右上角滑入。 */
import { reactive } from 'vue'

export const toasts = reactive([])
let seq = 0

function push(type, text, ms = 2600) {
  const id = ++seq
  toasts.push({ id, type, text })
  setTimeout(() => {
    const i = toasts.findIndex(t => t.id === id)
    if (i >= 0) toasts.splice(i, 1)
  }, ms)
}

export const toast = {
  success: (text) => push('success', text),
  error: (text) => push('error', text),
  info: (text) => push('info', text)
}
