<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { request, saveCurrentUser } from '../api'

const router = useRouter()
const form = ref({ username: '', password: '' })
const registerForm = ref({
  student_no: '',
  name: '',
  gender: '男',
  password: '',
  confirm_password: ''
})
const mode = ref('login')
const error = ref('')
const success = ref('')

async function submitLogin() {
  error.value = ''
  success.value = ''
  const result = await request('/login', {
    method: 'POST',
    body: JSON.stringify(form.value)
  })
  if (!result.success) {
    error.value = result.message
    return
  }
  saveCurrentUser(result.user, result.token)
  router.push(result.user.role === 'admin' ? '/admin' : '/student')
}

async function submitRegister() {
  error.value = ''
  success.value = ''
  if (registerForm.value.password !== registerForm.value.confirm_password) {
    error.value = '两次输入的密码不一致'
    return
  }
  const result = await request('/register', {
    method: 'POST',
    body: JSON.stringify({
      student_no: registerForm.value.student_no,
      name: registerForm.value.name,
      gender: registerForm.value.gender,
      password: registerForm.value.password
    })
  })
  if (!result.success) {
    error.value = result.message
    return
  }
  success.value = result.message
  form.value.username = registerForm.value.student_no
  form.value.password = ''
  mode.value = 'login'
}
</script>

<template>
  <div class="login-shell">
    <div class="login-card">
      <div class="login-hero">
        <div class="eyebrow">Admission Portal 2026</div>
        <h1>高校招生录取系统</h1>
        <p>面向招生办与考生的统一服务入口，录取数据、招生计划、公告通知集中管理。</p>
        <div class="login-highlights">
          <span>招生进度可视化</span>
          <span>考生服务大厅</span>
          <span>公告实时发布</span>
        </div>
        <div class="demo-account">演示账号：admin / 123456，2026001 / 123456</div>
      </div>
      <div class="login-panel">
        <div class="login-panel-head">
          <div>
            <div class="eyebrow">统一身份认证</div>
            <h2>登录系统</h2>
          </div>
          <span class="login-badge">安全入口</span>
        </div>
        <div class="auth-tabs">
          <button :class="{ active: mode === 'login' }" @click="mode = 'login'">账号登录</button>
          <button :class="{ active: mode === 'register' }" @click="mode = 'register'">学生注册</button>
        </div>
        <div v-if="error" class="error">{{ error }}</div>
        <div v-if="success" class="success">{{ success }}</div>

        <template v-if="mode === 'login'">
          <div class="field">
            <label>账号</label>
            <input v-model="form.username" class="input" placeholder="请输入账号" />
          </div>
          <div class="field">
            <label>密码</label>
            <input v-model="form.password" type="password" class="input" placeholder="请输入密码" />
          </div>
          <button class="btn login-submit" @click="submitLogin">登录系统</button>
        </template>

        <template v-else>
          <div class="field">
            <label>学号</label>
            <input v-model="registerForm.student_no" class="input" placeholder="请输入学号" />
          </div>
          <div class="form-grid compact">
            <div>
              <label>姓名</label>
              <input v-model="registerForm.name" class="input" placeholder="请输入姓名" />
            </div>
            <div>
              <label>性别</label>
              <select v-model="registerForm.gender" class="input">
                <option>男</option>
                <option>女</option>
              </select>
            </div>
          </div>
          <div class="field">
            <label>密码</label>
            <input v-model="registerForm.password" type="password" class="input" placeholder="请输入密码" />
          </div>
          <div class="field">
            <label>确认密码</label>
            <input v-model="registerForm.confirm_password" type="password" class="input" placeholder="请再次输入密码" />
          </div>
          <button class="btn login-submit" @click="submitRegister">注册学生账号</button>
        </template>
      </div>
    </div>
  </div>
</template>
