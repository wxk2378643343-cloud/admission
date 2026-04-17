<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AccountMenu from '../../components/AccountMenu.vue'
import { clearCurrentUser, getCurrentUser, request, saveCurrentUser } from '../../api'

const router = useRouter()
const user = ref(getCurrentUser())
const showProfileModal = ref(false)
const showPasswordModal = ref(false)
const profileForm = ref({ name: user.value?.name || '' })
const passwordForm = ref({ old_password: '', new_password: '' })
const profileMessage = ref('')
const passwordMessage = ref('')
const passwordError = ref('')

function logout() {
  clearCurrentUser()
  router.push('/login')
}

function openProfile() {
  profileMessage.value = ''
  profileForm.value.name = user.value?.name || ''
  showProfileModal.value = true
}

function openPassword() {
  passwordMessage.value = ''
  passwordError.value = ''
  passwordForm.value = { old_password: '', new_password: '' }
  showPasswordModal.value = true
}

async function submitProfile() {
  const result = await request('/profile', {
    method: 'PUT',
    body: JSON.stringify({
      user_id: user.value.id,
      name: profileForm.value.name
    })
  })
  if (result.success) {
    saveCurrentUser(result.user)
    user.value = result.user
    profileMessage.value = '个人信息已更新'
  }
}

async function submitPassword() {
  passwordError.value = ''
  passwordMessage.value = ''
  const result = await request('/student/password', {
    method: 'POST',
    body: JSON.stringify({
      user_id: user.value.id,
      ...passwordForm.value
    })
  })
  if (!result.success) {
    passwordError.value = result.message
    return
  }
  passwordMessage.value = result.message
}
</script>

<template>
  <div class="student-shell">
    <div class="student-wrap">
      <div class="student-topbar">
        <div class="student-brand">
          <span class="brand-mark">S</span>
          <div>
            <div class="eyebrow">Student Portal</div>
            <h2>考生服务大厅</h2>
          </div>
        </div>
        <nav>
          <router-link to="/student">首页</router-link>
          <router-link to="/student/profile">个人信息</router-link>
          <router-link to="/student/score">我的成绩</router-link>
          <router-link to="/student/choices">我的志愿</router-link>
          <router-link to="/student/admission">录取结果</router-link>
          <router-link to="/student/notices">公告通知</router-link>
        </nav>
        <AccountMenu
          :user="user"
          @profile="openProfile"
          @password="openPassword"
          @logout="logout"
        />
      </div>

      <section class="student-welcome">
        <div>
          <div class="eyebrow">Welcome Back</div>
          <h1>{{ user?.name }}，欢迎进入招生服务门户</h1>
          <p>查询个人信息、录取结果与招生公告，关键事项集中展示。</p>
        </div>
        <div class="welcome-card">
          <span>当前身份</span>
          <strong>考生</strong>
        </div>
      </section>
      <router-view />
    </div>
  </div>

  <div v-if="showProfileModal" class="modal-mask">
    <div class="modal-card account-modal">
      <div class="modal-head">
        <div>
          <div class="eyebrow">Account Profile</div>
          <h3>修改个人信息</h3>
        </div>
        <button class="ghost-close" @click="showProfileModal = false">×</button>
      </div>
      <div v-if="profileMessage" class="success">{{ profileMessage }}</div>
      <div class="field">
        <label>显示名称</label>
        <input v-model="profileForm.name" class="input" />
      </div>
      <div class="modal-actions">
        <button class="btn secondary" @click="showProfileModal = false">取消</button>
        <button class="btn" @click="submitProfile">保存</button>
      </div>
    </div>
  </div>

  <div v-if="showPasswordModal" class="modal-mask">
    <div class="modal-card account-modal">
      <div class="modal-head">
        <div>
          <div class="eyebrow">Account Security</div>
          <h3>修改密码</h3>
        </div>
        <button class="ghost-close" @click="showPasswordModal = false">×</button>
      </div>
      <div v-if="passwordError" class="error">{{ passwordError }}</div>
      <div v-if="passwordMessage" class="success">{{ passwordMessage }}</div>
      <div class="field">
        <label>原密码</label>
        <input v-model="passwordForm.old_password" type="password" class="input" />
      </div>
      <div class="field">
        <label>新密码</label>
        <input v-model="passwordForm.new_password" type="password" class="input" />
      </div>
      <div class="modal-actions">
        <button class="btn secondary" @click="showPasswordModal = false">取消</button>
        <button class="btn" @click="submitPassword">保存</button>
      </div>
    </div>
  </div>
</template>
