<template>
  <div class="toast-stack">
    <transition-group name="toast">
      <div v-for="t in toasts" :key="t.id" class="a-toast" :class="t.type">
        <span class="dot" />
        {{ t.text }}
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { toasts } from '../../stores/toast'
</script>

<style scoped>
.toast-stack {
  position: fixed; top: 20px; left: 50%; transform: translateX(-50%);
  display: flex; flex-direction: column; gap: 8px; z-index: 200; pointer-events: none;
  align-items: center;
}
.a-toast {
  display: flex; align-items: center; gap: 8px;
  background: rgba(29, 29, 31, 0.92); color: #fff;
  padding: 10px 20px; border-radius: var(--radius-pill);
  font-size: var(--fs-small); box-shadow: 0 8px 28px rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(10px); max-width: min(90vw, 480px);
}
.dot { width: 7px; height: 7px; border-radius: 50%; background: var(--c-blue); flex-shrink: 0; }
.a-toast.success .dot { background: var(--c-green); }
.a-toast.error .dot { background: var(--c-red); }
.toast-enter-active { transition: all var(--t-slow) var(--ease); }
.toast-leave-active { transition: all var(--t-base) var(--ease); }
.toast-enter-from { opacity: 0; transform: translateY(-12px); }
.toast-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
