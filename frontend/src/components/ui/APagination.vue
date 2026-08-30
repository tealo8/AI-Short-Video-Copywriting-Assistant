<template>
  <div class="a-pagination">
    <button class="pg-btn" :disabled="page <= 1" @click="go(page - 1)">‹ 上一页</button>
    <template v-for="(p, i) in pageList" :key="i">
      <span v-if="p === '...'" class="pg-ellipsis">…</span>
      <button v-else class="pg-btn num" :class="{ on: p === page }" @click="go(p)">{{ p }}</button>
    </template>
    <button class="pg-btn" :disabled="page >= maxPage" @click="go(page + 1)">下一页 ›</button>
    <span class="pg-info helper-text">共 {{ total }} 条 / {{ maxPage }} 页</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 12 }
})
const emit = defineEmits(['update:page', 'change'])

const maxPage = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

/** 页码窗口：当前页 ±2，首尾直达，中间省略号 */
const pageList = computed(() => {
  const max = maxPage.value
  if (max <= 7) return Array.from({ length: max }, (_, i) => i + 1)
  const cur = props.page
  const pages = new Set([1, 2, max - 1, max, cur - 1, cur, cur + 1])
  const list = [...pages].filter(p => p >= 1 && p <= max).sort((a, b) => a - b)
  const out = []
  let prev = 0
  for (const p of list) {
    if (p - prev > 1) out.push('...')
    out.push(p)
    prev = p
  }
  return out
})

const go = (p) => {
  if (p < 1 || p > maxPage.value || p === props.page) return
  emit('update:page', p)
  emit('change', p)
}
</script>

<style scoped>
.a-pagination { display: flex; align-items: center; justify-content: center; gap: 6px; flex-wrap: wrap; }
.pg-btn {
  min-width: 34px; height: 34px; padding: 0 12px; border-radius: 9px;
  background: var(--c-bg); color: var(--c-ink); font-size: var(--fs-small);
  transition: all var(--t-base) var(--ease);
}
.pg-btn:hover:not(:disabled) { background: #e8ebee; }
.pg-btn.on { background: var(--c-blue); color: #fff; font-weight: 600; }
.pg-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.pg-ellipsis { color: var(--c-gray); padding: 0 2px; }
.pg-info { margin-left: 8px; font-variant-numeric: tabular-nums; }
</style>
