<template>
  <button class="a-switch" :class="{ on: modelValue }" @click="$emit('update:modelValue', !modelValue)"
    role="switch" :aria-checked="modelValue">
    <span class="knob" />
  </button>
</template>

<script setup>
defineProps({ modelValue: Boolean })
defineEmits(['update:modelValue'])
</script>

<style scoped>
.a-switch {
  width: 44px; height: 26px; border-radius: 20px; background: var(--c-gray-light);
  position: relative; transition: background var(--t-base) var(--ease); flex-shrink: 0;
}
.a-switch.on { background: var(--c-blue); }
.knob {
  position: absolute; top: 3px; left: 3px; width: 20px; height: 20px; border-radius: 50%;
  background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.18);
  transition: transform var(--t-base) var(--ease);
}
.a-switch.on .knob { transform: translateX(18px); }
</style>
