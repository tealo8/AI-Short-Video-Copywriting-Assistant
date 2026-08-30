<template>
  <div class="a-field">
    <label v-if="label" class="a-label">{{ label }}
      <span v-if="count" class="count">{{ valueLength }} / {{ maxlength }}</span>
    </label>
    <div class="a-textarea-wrap">
      <textarea class="a-textarea" :value="modelValue" :rows="rows"
        :placeholder="placeholder" :maxlength="maxlength" :disabled="disabled"
        @input="$emit('update:modelValue', $event.target.value)" />
    </div>
    <p v-if="hint" class="helper-text mt-8">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  modelValue: String, label: String, placeholder: String,
  rows: { type: Number, default: 5 }, maxlength: Number, disabled: Boolean,
  hint: String, count: Boolean
})
defineEmits(['update:modelValue'])
const valueLength = computed(() => (props.modelValue || '').length)
</script>

<style scoped>
.a-field { width: 100%; min-width: 0; }
.a-label { display: flex; justify-content: space-between; font-size: var(--fs-small); font-weight: 600; color: var(--c-ink); margin-bottom: 8px; line-height: 1.5; min-height: 1.5em; }
.count { font-weight: 400; color: var(--c-gray); }
.a-textarea-wrap { background: var(--c-bg); border-radius: var(--radius-md); border: 1px solid transparent; transition: all var(--t-base) var(--ease); }
.a-textarea-wrap:focus-within { background: #fff; border-color: var(--c-blue); box-shadow: 0 0 0 3px var(--c-blue-soft); }
.a-textarea {
  display: block; width: 100%; border: none; outline: none; background: transparent; resize: vertical;
  padding: 13px 16px; font-size: var(--fs-body); line-height: 1.7; color: var(--c-ink);
  min-height: 96px; overflow-y: auto;   /* 独立滚动，防止塌陷 */
}
.a-textarea::placeholder { color: var(--c-gray); opacity: 0.75; }
</style>
