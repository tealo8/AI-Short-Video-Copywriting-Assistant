<template>
  <div class="a-progress">
    <div class="track">
      <div class="bar" :style="{ width: pct + '%' }" :class="{ indeterminate: !modelValue && indeterminate }" />
    </div>
    <span class="pct">{{ pct }}%</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  value: { type: Number, default: 0 },   // 0-100
  indeterminate: Boolean
})
const pct = computed(() => Math.max(0, Math.min(100, Math.round(props.value))))
</script>

<style scoped>
.a-progress { display: flex; align-items: center; gap: 12px; }
.track { flex: 1; height: 5px; background: var(--c-gray-light); border-radius: 5px; overflow: hidden; }
.bar {
  height: 100%; border-radius: 5px; background: var(--c-blue);
  transition: width var(--t-slow) var(--ease);
}
.bar.indeterminate {
  width: 30% !important; background: linear-gradient(90deg, var(--c-blue-soft), var(--c-blue), var(--c-blue-soft));
  animation: slide 1.2s infinite var(--ease);
}
@keyframes slide { 0% { margin-left: -30%; } 100% { margin-left: 100%; } }
.pct { font-size: var(--fs-small); color: var(--c-gray); min-width: 38px; text-align: right; font-variant-numeric: tabular-nums; }
</style>
