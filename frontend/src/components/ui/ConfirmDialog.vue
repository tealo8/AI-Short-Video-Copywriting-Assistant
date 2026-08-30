<template>
  <Teleport to="body">
    <div v-if="confirmState.visible" class="confirm-mask" @click.self="resolveConfirm(false)">
      <div class="confirm-box">
        <div class="icon" :class="{ danger: confirmState.danger }">{{ confirmState.danger ? '⚠️' : '❓' }}</div>
        <h3>{{ confirmState.title }}</h3>
        <p>{{ confirmState.message }}</p>
        <div class="btns">
          <AButton kind="secondary" @click="resolveConfirm(false)">{{ confirmState.cancelText }}</AButton>
          <AButton :kind="confirmState.danger ? 'danger' : 'primary'" @click="resolveConfirm(true)">{{ confirmState.okText }}</AButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import AButton from './AButton.vue'
import { confirmState, resolveConfirm } from '../../stores/confirm'
</script>

<style scoped>
.confirm-mask {
  position: fixed; inset: 0; z-index: 150;
  background: rgba(0, 0, 0, 0.32); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.confirm-box {
  width: 100%; max-width: 380px; background: #fff; border-radius: 20px;
  padding: 30px 28px 24px; text-align: center; box-shadow: 0 24px 64px rgba(0, 0, 0, 0.2);
  animation: rise var(--t-slow) var(--ease);
}
@keyframes rise { from { opacity: 0; transform: scale(0.96) translateY(8px); } to { opacity: 1; transform: none; } }
.icon { font-size: 34px; margin-bottom: 12px; }
h3 { font-size: 17px; margin-bottom: 8px; }
p { color: var(--c-gray); font-size: var(--fs-small); line-height: 1.7; }
.btns { display: flex; gap: 10px; margin-top: 22px; justify-content: center; }
</style>
