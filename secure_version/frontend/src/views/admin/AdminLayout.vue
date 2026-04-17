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
    body: JSON.stringify(passwordForm.value)
  })
  if (!result.success) {
    passwordError.value = result.message
    return
  }
  passwordMessage.value = result.message
}
</script>

<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="admin-brand">
        <span class="brand-mark">A</span>
        <span>招生录取系统</span>
      </div>
      <div class="admin-side-caption">Admissions Office</div>
      <nav class="admin-nav">
        <router-link to="/admin">后台首页</router-link>
        <router-link to="/admin/students">学生信息管理</router-link>
        <router-link to="/admin/scores">学生成绩管理</router-link>
        <router-link to="/admin/plans">招生计划管理</router-link>
        <router-link to="/admin/choices">志愿管理</router-link>
        <router-link to="/admin/admissions">录取分配</router-link>
        <router-link to="/admin/notices">公告管理</router-link>
      </nav>
    </aside>
    <main class="admin-main">
      <div class="topbar">
        <div>
          <div class="eyebrow">Management Console</div>
          <h2>后台管理中心</h2>
          <div class="meta">招生数据、计划、录取结果与公告发布统一维护</div>
        </div>
        <AccountMenu
          :user="user"
          @profile="openProfile"
          @password="openPassword"
          @logout="logout"
        />
      </div>
      <router-view />
    </main>
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
