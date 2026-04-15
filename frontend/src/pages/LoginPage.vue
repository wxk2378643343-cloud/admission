<template>
  <div class="auth-page">
    <section class="auth-left">
      <h1>高校招生录取系统</h1>
      <p>Graduation Demo · Insecure Version</p>
      <ul>
        <li>SQL 注入演示点</li>
        <li>越权访问演示点</li>
        <li>存储型 XSS 演示点</li>
        <li>暴力破解风险演示点</li>
      </ul>
    </section>
    <section class="auth-right">
      <div class="login-card">
        <div class="auth-title">
          <h2>{{ authMode === 'login' ? '系统登录' : '注册账号' }}</h2>
          <p class="muted">演示账号：admin/admin123，alice/123456，bob/123456</p>
        </div>
        <template v-if="authMode === 'login'">
          <label><span>用户名</span><input v-model="loginForm.username" placeholder="请输入用户名" /></label>
          <label><span>密码</span><input type="password" v-model="loginForm.password" placeholder="请输入密码" /></label>
          <div class="auth-actions">
            <button class="btn primary" @click="login">登录</button>
            <button class="btn ghost" @click="authMode = 'register'">去注册</button>
          </div>
        </template>
        <template v-else>
          <div class="auth-grid">
            <label><span>用户名</span><input v-model="registerForm.username" placeholder="请输入用户名" /></label>
            <label><span>密码</span><input type="password" v-model="registerForm.password" placeholder="请输入密码" /></label>
            <label><span>姓名</span><input v-model="registerForm.name" placeholder="请输入姓名" /></label>
            <label><span>身份证号</span><input v-model="registerForm.id_card" placeholder="请输入身份证号" /></label>
            <label><span>手机号</span><input v-model="registerForm.phone" placeholder="请输入手机号" /></label>
          </div>
          <div class="auth-actions">
            <button class="btn primary" @click="register">提交注册</button>
            <button class="btn ghost" @click="authMode = 'login'">返回登录</button>
          </div>
        </template>
        <p class="error">{{ msg }}</p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const API_BASE = 'http://127.0.0.1:8000'
const router = useRouter()

const msg = ref('')
const authMode = ref('login')
const loginForm = reactive({ username: 'admin', password: 'admin123' })
const registerForm = reactive({
  username: '',
  password: '',
  name: '',
  id_card: '',
  phone: ''
})

async function readError(res) {
  try {
    const data = await res.json()
    return data.detail || JSON.stringify(data)
  } catch {
    return await res.text()
  }
}

async function apiPost(path, payload) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

async function login() {
  try {
    msg.value = ''
    const data = await apiPost('/api/login', loginForm)
    localStorage.setItem('admission_user', JSON.stringify(data))
    router.replace('/dashboard')
  } catch (e) {
    msg.value = '登录失败：' + e.message
  }
}

async function register() {
  try {
    msg.value = ''
    const usernameOk = /^[a-zA-Z0-9_]{4,20}$/.test(registerForm.username.trim())
    if (!usernameOk) {
      msg.value = '注册失败：用户名需为4-20位字母/数字/下划线'
      return
    }
    if ((registerForm.password || '').length < 6) {
      msg.value = '注册失败：密码长度至少6位'
      return
    }
    if (!registerForm.name.trim()) {
      msg.value = '注册失败：姓名不能为空'
      return
    }
    if (!/^\d{17}[\dXx]$/.test(registerForm.id_card.trim())) {
      msg.value = '注册失败：身份证号格式不正确'
      return
    }
    if (!/^1\d{10}$/.test(registerForm.phone.trim())) {
      msg.value = '注册失败：手机号格式不正确'
      return
    }

    const result = await apiPost('/api/register', registerForm)
    loginForm.username = registerForm.username
    loginForm.password = registerForm.password
    authMode.value = 'login'
    msg.value = `注册成功，准考证号：${result.exam_no}`
  } catch (e) {
    msg.value = '注册失败：' + e.message
  }
}

onMounted(() => {
  const cache = localStorage.getItem('admission_user')
  if (cache) {
    router.replace('/dashboard')
  }
})
</script>
