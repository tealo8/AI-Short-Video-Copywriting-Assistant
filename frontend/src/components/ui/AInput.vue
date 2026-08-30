<template>
  <div class="a-field">
    <label v-if="label" class="a-label" :for="id">{{ label }}</label>
    <div class="a-input-wrap" :class="{ focus: focused, error }">
      <input :id="id" class="a-input" :value="modelValue" :type="type"
        :placeholder="placeholder" :disabled="disabled" :maxlength="maxlength"
        @input="$emit('update:modelValue', $event.target.value)"
        @focus="focused = true" @blur="focused = false" />
      <span v-if="suffix" class="a-suffix">{{ suffix }}</span>
    </div>
    <p v-if="hint" class="helper-text mt-8">{{ hint }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
defineProps({
  modelValue: [String, Number],
  label: String, placeholder: String, type: { type: String, default: 'text' },
  hint: String, suffix: String, disabled: Boolean, error: Boolean, maxlength: Number
})
defineEmits(['update:modelValue'])
const focused = ref(false)
const id = `a-input-${Math.random().toString(36).slice(2, 8)}`
</script>

<style scoped>
.a-field { width: 100%; }
.a-label { display: block; font-size: var(--fs-small); font-weight: 600; color: var(--c-ink); margin-bottom: 8px; }
.a-input-wrap {
  display: flex; align-items: center;
  background: var(--c-bg);
  border-radius: var(--radius-md);
  transition: box-shadow var(--t-base) var(--ease), background var(--t-base) var(--ease);
  border: 1px solid transparent;
}
.a-input-wrap:focus-within, .a-input-wrap.focus { background: #fff; border-color: var(--c-blue); box-shadow: 0 0 0 3px var(--c-blue-soft); }
.a-input-wrap.error { border-color: var(--c-red); }
.a-input {
  flex: 1; border: none; outline: none; background: transparent;
  height: 42px; padding: 0 16px; font-size: var(--fs-body); color: var(--c-ink);
}
.a-input::placeholder { color: var(--c-gray); opacity: 0.75; }
.a-suffix { padding-right: 14px; font-size: var(--fs-small); color: var(--c-gray); }
</style>
