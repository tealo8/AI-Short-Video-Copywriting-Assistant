<template>
  <div class="a-card" :class="{ hover, flat, padded: !paddingless }">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  hover: Boolean,     // 悬浮上浮
  flat: Boolean,      // 无阴影（浅灰底）
  paddingless: Boolean
})
</script>

<style scoped>
.a-card {
  background: var(--c-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  transition: transform var(--t-base) var(--ease), box-shadow var(--t-base) var(--ease);
}
.a-card.padded { padding: 28px; }
.a-card.hover:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
.a-card.flat { box-shadow: none; background: var(--c-bg); }
@media (max-width: 640px) { .a-card.padded { padding: 20px; } }
</style>
