<template>
  <ACard>
    <div class="sec-head">
      <h3 class="section-title">{{ title }}</h3>
      <div class="spacer" />
      <CopyBtn v-if="text" :text="text" />
    </div>
    <div :class="['body', { highlight }]"><p>{{ text || '—' }}</p></div>
  </ACard>
</template>

<script setup>
import ACard from './ui/ACard.vue'
import CopyBtn from './ui/CopyBtn.vue'
defineProps({ title: String, text: String, highlight: Boolean })
</script>

<style scoped>
.sec-head { display: flex; align-items: center; gap: 12px; }
.spacer { flex: 1; }
.body { margin-top: 14px; background: var(--c-bg); border-radius: var(--radius-md); padding: 16px 18px; }
.body p { font-size: var(--fs-body); line-height: 1.8; }
.body.highlight { background: var(--c-blue-soft); }
.body.highlight p { color: var(--c-blue); font-weight: 500; }
</style>
