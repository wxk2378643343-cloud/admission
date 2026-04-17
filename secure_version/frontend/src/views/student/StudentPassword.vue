<script setup>
import { ref } from 'vue'
import { getCurrentUser, request } from '../../api'

const form = ref({
  old_password: '',
  new_password: ''
})
const error = ref('')
const success = ref('')

async function submitPassword() {
  error.value = ''
  success.value = ''
  const result = await request('/student/password', {
    method: 'POST',
    body: JSON.stringify(form.value)
  })
  if (!result.success) {
    error.value = result.message
    return
  }
  success.value = result.message
}
</script>

<template>
  <div class="student-card password-card">
    <div class="eyebrow">Account Security</div>
    <h3>修改密码</h3>
    <p class="meta">建议定期更换密码，避免使用与其他平台相同的密码。</p>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="success" class="success">{{ success }}</div>
    <div class="field">
      <label>原密码</label>
      <input v-model="form.old_password" type="password" class="input" />
    </div>
    <div class="field">
      <label>新密码</label>
      <input v-model="form.new_password" type="password" class="input" />
    </div>
    <button class="btn" @click="submitPassword">提交</button>
  </div>
</template>
