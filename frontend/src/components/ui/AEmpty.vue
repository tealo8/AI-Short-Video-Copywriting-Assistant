<template>
  <div class="a-empty">
    <div class="icon">📄</div>
    <p class="text">{{ text }}</p>
    <p v-if="hint" class="helper-text">{{ hint }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({ text: { type: String, default: '暂无内容' }, hint: String })
</script>

<style scoped>
.a-empty { text-align: center; padding: 56px 24px; }
.icon { font-size: 34px; margin-bottom: 14px; opacity: 0.5; }
.text { color: var(--c-ink); font-size: var(--fs-body); font-weight: 500; }
.helper-text { margin-top: 6px; }
</style>
