<template>
  <div class="a-select">
    <label v-if="label" class="a-label">{{ label }}</label>
    <div ref="triggerRef" class="sel-wrap" :class="{ open }" @click="toggle">
      <span class="sel-value" :class="{ placeholder: !current }">{{ current || placeholder }}</span>
      <svg class="carat" :class="{ up: open }" width="12" height="12" viewBox="0 0 12 12">
        <path d="M2 4l4 4 4-4" stroke="#86868b" stroke-width="1.6" fill="none" stroke-linecap="round"/>
      </svg>
    </div>

    <!-- 面板挂载到 body + fixed 定位：不被父容器 overflow/层级裁剪 -->
    <Teleport to="body">
      <transition name="pop">
        <div v-if="open" ref="panelRef" class="sel-panel" :style="panelStyle">
          <div v-for="opt in options" :key="opt.value" class="sel-option"
            :class="{ selected: opt.value === modelValue }" @click="pick(opt)">
            <span>{{ opt.label }}</span>
            <span v-if="opt.color" class="dot" :style="{ background: opt.color }" />
          </div>
          <div v-if="!options.length" class="sel-empty helper-text">暂无选项</div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  modelValue: String,
  label: String,
  placeholder: { type: String, default: '请选择' },
  options: { type: Array, default: () => [] }   // [{label, value, color?}]
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const triggerRef = ref(null)
const panelRef = ref(null)
const panelStyle = ref({})

const current = computed(() => props.options.find(o => o.value === props.modelValue)?.label)

const updatePanelPos = () => {
  const el = triggerRef.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const spaceBelow = window.innerHeight - rect.bottom
  const spaceAbove = rect.top
  const maxH = Math.max(220, Math.min(360, Math.max(spaceBelow - 12, spaceAbove - 12)))
  const openUp = spaceBelow < 260 && spaceAbove > spaceBelow
  panelStyle.value = {
    top: openUp ? 'auto' : `${rect.bottom + 6}px`,
    bottom: openUp ? `${window.innerHeight - rect.top + 6}px` : 'auto',
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    maxHeight: `${maxH}px`
  }
}

const toggle = () => {
  if (!open.value) updatePanelPos()
  open.value = !open.value
}

/** 文档级点击：仅当点击发生在组件（触发区/面板）之外时才关闭，
    修复此前"点击触发区→toggle 开→冒泡到 document→立即 close"导致的无法展开 */
const onDocClick = (e) => {
  if (!open.value) return
  const inside =
    (triggerRef.value && triggerRef.value.contains(e.target)) ||
    (panelRef.value && panelRef.value.contains(e.target))
  if (!inside) open.value = false
}

/** 滚动关闭：仅当滚动发生在面板【之外】才关闭下拉；
    面板自身为 overflow:auto，内部滚动必须保持展开（此前捕获阶段监听会误杀面板滚动） */
const onScrollClose = (e) => {
  if (!open.value) return
  const t = e.target
  if (panelRef.value && (t === panelRef.value || panelRef.value.contains(t))) return
  open.value = false
}

const pick = (opt) => {
  emit('update:modelValue', opt.value)
  open.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  window.addEventListener('scroll', onScrollClose, true)
  window.addEventListener('resize', onScrollClose)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  window.removeEventListener('scroll', onScrollClose, true)
  window.removeEventListener('resize', onScrollClose)
})
</script>

<style scoped>
.a-select { position: relative; }
.a-label { display: block; font-size: var(--fs-small); font-weight: 600; color: var(--c-ink); margin-bottom: 8px; }
.sel-wrap {
  display: flex; align-items: center; justify-content: space-between;
  height: 42px; padding: 0 16px; background: var(--c-bg); border-radius: var(--radius-md);
  cursor: pointer; border: 1px solid transparent;
  transition: background var(--t-base) var(--ease), border-color var(--t-base) var(--ease);
}
.sel-wrap:hover { background: #eef0f2; }
.sel-wrap.open { background: #fff; border-color: var(--c-blue); box-shadow: 0 0 0 3px var(--c-blue-soft); }
.sel-value { font-size: var(--fs-body); color: var(--c-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sel-value.placeholder { color: var(--c-gray); }
.carat { transition: transform var(--t-base) var(--ease); flex-shrink: 0; margin-left: 8px; }
.carat.up { transform: rotate(180deg); }

/* -------- Teleport 到 body 的面板（fixed 定位，脱离父容器） -------- */
.sel-panel {
  position: fixed; z-index: 300;
  background: #fff; border-radius: var(--radius-md);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08), 0 20px 48px rgba(0, 0, 0, 0.14);
  padding: 6px; overflow: auto;
  overscroll-behavior: contain;   /* 面板内滚动不滚到页面，且不会触发外层滚动 */
  touch-action: pan-y;
}
.sel-option {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border-radius: 8px; font-size: var(--fs-body); cursor: pointer;
  transition: background var(--t-fast) var(--ease);
}
.sel-option:hover { background: var(--c-bg); }
.sel-option.selected { color: var(--c-blue); font-weight: 600; }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.sel-empty { padding: 12px; text-align: center; }
.pop-enter-active, .pop-leave-active { transition: opacity var(--t-fast) var(--ease), transform var(--t-fast) var(--ease); }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
