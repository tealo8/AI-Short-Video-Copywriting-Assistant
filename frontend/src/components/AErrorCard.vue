<template>
  <div class="error-card">
    <div class="icon">🤖</div>
    <h3>{{ title }}</h3>
    <p class="msg">{{ message || 'AI 调用失败，内容生成未完成' }}</p>
    <ul v-if="tips && tips.length" class="tips">
      <li v-for="(t, i) in tips" :key="i">{{ t }}</li>
    </ul>
    <div class="actions">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '生成失败' },
  message: String,
  tips: { type: Array, default: () => [] }
})
</script>

<style scoped>
.error-card {
  background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-card);
  padding: 44px 28px; text-align: center;
}
.icon { font-size: 38px; margin-bottom: 12px; }
h3 { font-size: 17px; margin-bottom: 8px; }
.msg { color: var(--c-gray); max-width: 420px; margin: 0 auto; line-height: 1.8; font-size: var(--fs-small); }
.tips {
  text-align: left; max-width: 480px; margin: 16px auto 0; list-style: none;
  background: var(--c-bg); border-radius: var(--radius-md); padding: 12px 16px;
  color: var(--c-gray); font-size: var(--fs-tiny); line-height: 2.1;
}
.tips li::before { content: '· '; color: var(--c-blue); }
.actions { margin-top: 20px; display: flex; justify-content: center; gap: 10px; }
</style>
