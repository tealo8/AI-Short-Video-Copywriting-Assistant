<template>
  <button class="a-btn" :class="[kind, size, { loading, disabled: disabled || loading }]"
    :disabled="disabled || loading" @click="$emit('click', $event)">
    <span v-if="loading" class="btn-spinner" />
    <slot />
  </button>
</template>

<script setup>
defineProps({
  kind: { type: String, default: 'primary' },   // primary | secondary | ghost | danger | success
  size: { type: String, default: 'md' },        // sm | md | lg
  loading: Boolean,
  disabled: Boolean
})
defineEmits(['click'])
</script>

<style scoped>
.a-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  border-radius: var(--radius-md);
  font-weight: 500; letter-spacing: 0.01em;
  transition: transform var(--t-fast) var(--ease), background var(--t-base) var(--ease),
    box-shadow var(--t-base) var(--ease), opacity var(--t-base) var(--ease);
  user-select: none; white-space: nowrap;
}
/* 主按钮：纯色苹果蓝、白字、无描边、hover 悬浮 + 透明度微调 */
.a-btn.primary { background: var(--c-blue); color: #fff; }
.a-btn.primary:hover { background: var(--c-blue-hover); transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0, 113, 227, 0.25); }
/* 次按钮：白底、浅灰描边、hover 底色微变 */
.a-btn.secondary { background: var(--c-white); color: var(--c-ink); border: 1px solid var(--c-gray-light); }
.a-btn.secondary:hover { background: #f5f5f7; }
.a-btn.ghost { color: var(--c-blue); background: transparent; }
.a-btn.ghost:hover { background: var(--c-blue-soft); }
.a-btn.danger { background: #fff; color: var(--c-red); border: 1px solid #ffd2cf; }
.a-btn.danger:hover { background: #fff0ef; }
.a-btn.success { background: var(--c-green); color: #fff; }
/* 尺寸 */
.a-btn.sm { height: 30px; padding: 0 14px; font-size: var(--fs-small); border-radius: 10px; }
.a-btn.md { height: 38px; padding: 0 20px; font-size: var(--fs-body); }
.a-btn.lg { height: 46px; padding: 0 28px; font-size: 16px; }
/* 点击：轻微缩放回弹 */
.a-btn:not(:disabled):active { transform: scale(0.97); }
.a-btn.disabled, .a-btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none !important; }
.btn-spinner {
  width: 13px; height: 13px; border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.35); border-top-color: #fff;
  animation: softSpin 0.8s linear infinite;
}
</style>
