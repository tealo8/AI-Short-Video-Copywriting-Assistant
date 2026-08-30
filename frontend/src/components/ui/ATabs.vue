<template>
  <div class="a-tabs">
    <div class="tab" v-for="t in tabs" :key="t.value" :class="{ active: t.value === modelValue }"
      @click="$emit('update:modelValue', t.value)">
      {{ t.label }}
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: String,
  tabs: { type: Array, default: () => [] }   // [{label, value}]
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.a-tabs {
  display: inline-flex; padding: 4px; background: var(--c-bg); border-radius: 12px;
  transition: background var(--t-base) var(--ease);
}
.tab {
  padding: 7px 18px; border-radius: 9px; font-size: var(--fs-small); font-weight: 500;
  color: var(--c-gray); cursor: pointer; transition: all var(--t-base) var(--ease);
  user-select: none; white-space: nowrap;
}
.tab:hover { color: var(--c-ink); }
.tab.active { background: #fff; color: var(--c-ink); font-weight: 600; box-shadow: 0 1px 5px rgba(0,0,0,0.08); }
</style>
