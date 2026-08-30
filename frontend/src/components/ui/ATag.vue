<template>
  <span class="a-tag" :class="tone">{{ text }}</span>
</template>

<script setup>
defineProps({ text: String, tone: { type: String, default: 'blue' } })  // blue | gray | green | amber | red
</script>

<style scoped>
.a-tag {
  display: inline-flex; align-items: center; padding: 3px 12px; border-radius: var(--radius-pill);
  font-size: var(--fs-tiny); font-weight: 500; line-height: 1.5;
  white-space: nowrap; flex-shrink: 0;   /* 标签文字禁止换行：避免表格窄列下"出/镜"竖排 */
  background: var(--c-blue-soft); color: var(--c-blue);
}
.a-tag.gray { background: var(--c-bg); color: var(--c-gray); }
.a-tag.green { background: rgba(52, 199, 89, 0.1); color: #248a3d; }
.a-tag.amber { background: rgba(255, 159, 10, 0.12); color: #b26a00; }
.a-tag.red { background: rgba(255, 59, 48, 0.1); color: #d70015; }
</style>
