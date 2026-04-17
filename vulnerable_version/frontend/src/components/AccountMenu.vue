<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

defineProps({
  user: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['profile', 'password', 'logout'])
const open = ref(false)
const root = ref(null)

function toggleMenu() {
  open.value = !open.value
}

function closeMenu() {
  open.value = false
}

function handleAction(action) {
  closeMenu()
  emit(action)
}

function handleDocumentClick(event) {
  if (!root.value?.contains(event.target)) {
    closeMenu()
  }
}

function handleKeydown(event) {
  if (event.key === 'Escape') {
    closeMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div ref="root" class="account-menu" :class="{ open }">
    <button class="account-trigger" type="button" @click.stop="toggleMenu">
      <span class="avatar">{{ user?.name?.slice(0, 1) || 'U' }}</span>
      <span class="account-name">{{ user?.name }}</span>
      <span class="chevron">⌄</span>
    </button>
    <div class="account-dropdown">
      <button type="button" @click="handleAction('profile')">修改个人信息</button>
      <button type="button" @click="handleAction('password')">修改密码</button>
      <button type="button" class="danger" @click="handleAction('logout')">退出登录</button>
    </div>
  </div>
</template>
