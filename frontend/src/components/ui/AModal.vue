<template>
  <teleport to="body">
    <transition name="modal">
      <div v-if="modelValue" class="a-modal-mask" @click.self="$emit('update:modelValue', false)">
        <div class="a-modal" :style="{ maxWidth: width + 'px' }">
          <div class="modal-head">
            <h3>{{ title }}</h3>
            <button class="close" @click="$emit('update:modelValue', false)">✕</button>
          </div>
          <div class="modal-body"><slot /></div>
          <div v-if="$slots.footer" class="modal-foot"><slot name="footer" /></div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
defineProps({
  modelValue: Boolean, title: String,
  width: { type: Number, default: 560 }
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.a-modal-mask {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.32);
  display: flex; align-items: center; justify-content: center; z-index: 100;
  backdrop-filter: blur(6px); padding: 20px;
}
.a-modal {
  width: 100%; background: #fff; border-radius: 20px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.2); overflow: hidden;
  animation: rise var(--t-slow) var(--ease);
}
@keyframes rise { from { opacity: 0; transform: translateY(14px) scale(0.98); } to { opacity: 1; transform: none; } }
.modal-head { display: flex; align-items: center; justify-content: space-between; padding: 22px 26px 0; }
.modal-head h3 { font-size: var(--fs-module); font-weight: 700; }
.close { color: var(--c-gray); font-size: 14px; padding: 6px 10px; border-radius: 8px; transition: background var(--t-fast); }
.close:hover { background: var(--c-bg); }
.modal-body { padding: 18px 26px 26px; max-height: 66vh; overflow: auto; }
.modal-foot { padding: 0 26px 24px; display: flex; justify-content: flex-end; gap: 10px; }
.modal-enter-active, .modal-leave-active { transition: opacity var(--t-base) var(--ease); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
