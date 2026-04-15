<template>
  <div v-if="user" class="layout">
    <aside class="sidebar">
      <div class="brand">
        <strong>招生录取后台</strong>
        <small>研究演示环境</small>
      </div>
      <nav>
        <button v-for="item in visibleNavItems" :key="item.key" :class="['nav-btn', { active: activeSection === item.key }]" @click="activeSection = item.key">
          {{ item.label }}
        </button>
      </nav>
      <div class="side-note">
        <p>当前角色：{{ user.role }}</p>
        <p>修复版本，用于安全方案验证。</p>
      </div>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <h2>{{ currentTitle }}</h2>
          <p>{{ currentDesc }}</p>
        </div>
        <div class="top-actions">
          <div class="user-menu">
            <span class="chip user-chip">{{ user.username }}</span>
            <div class="menu-panel">
              <button class="menu-item" @click="openMyProfileEdit">编辑个人信息</button>
              <button class="menu-item danger" @click="logout">退出登录</button>
            </div>
          </div>
        </div>
      </header>

      <p v-if="actionMsg" class="ok-banner">{{ actionMsg }}</p>

      <section v-if="activeSection === 'overview'" class="page-grid">
        <article class="metric card"><h3>考生档案</h3><strong>{{ profiles.length }}</strong></article>
        <article class="metric card"><h3>志愿记录</h3><strong>{{ choices.length }}</strong></article>
        <article class="metric card"><h3>有成绩考生数</h3><strong>{{ scoredCandidateCount }}</strong></article>
        <article class="metric card"><h3>录取记录</h3><strong>{{ admissions.length }}</strong></article>
      </section>
      <OverviewCharts
        v-if="activeSection === 'overview'"
        :admission-stats="admissionStats"
        :score-buckets="scoreBuckets"
      />

      <section v-if="activeSection === 'profiles'" class="card">
        <SectionHeader title="考生表格">
          <template #actions>
            <button v-if="isAdmin" class="btn primary" @click="openProfileCreate">新增/导入考生</button>
            <button class="btn ghost small" @click="loadProfiles">刷新</button>
          </template>
        </SectionHeader>
        <table class="table">
          <thead><tr><th>ID</th><th>姓名</th><th>准考证</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="p in visibleProfiles" :key="p.id">
              <td>{{ p.id }}</td><td>{{ p.name }}</td><td>{{ p.exam_no }}</td>
              <td>
                <div class="toolbar-inline">
                  <button class="btn ghost small" @click="openProfileModal(p)">查看</button>
                  <button v-if="isAdmin" class="btn ghost small" @click="openProfileEdit(p)">编辑</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section v-if="activeSection === 'choices'" class="card">
        <SectionHeader title="志愿填报表格">
          <template #actions>
            <template v-if="isCandidate">
              <button
                v-if="!candidateChoiceLocked"
                class="btn primary"
                @click="openChoiceCreate"
              >
                填报志愿
              </button>
              <span v-else :title="candidateChoiceLockReason" style="display:inline-flex;cursor:not-allowed;">
                <button class="btn primary" disabled>填报志愿</button>
              </span>
            </template>
            <button class="btn ghost small" @click="loadChoices">刷新</button>
          </template>
        </SectionHeader>
        <table class="table">
          <thead><tr><th>ID</th><th>考生ID</th><th>批次</th><th>院校</th><th>专业</th><th>优先级</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="c in visibleChoices" :key="c.id">
              <td>{{ c.id }}</td><td>{{ c.candidate_id }}</td><td>{{ c.batch }}</td><td>{{ c.university }}</td><td>{{ c.major }}</td><td>{{ c.priority }}</td>
              <td>
                <div class="toolbar-inline">
                  <template v-if="isCandidate">
                    <button v-if="!candidateChoiceLocked" class="btn ghost small" @click="openChoiceEdit(c)">编辑</button>
                    <span v-else :title="candidateChoiceLockReason" style="display:inline-flex;cursor:not-allowed;">
                      <button class="btn ghost small" disabled>编辑</button>
                    </span>
                  </template>
                  <button v-if="isAdmin" class="btn ghost small" @click="goAdmissionFromChoice(c)">进入录取</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <ScoresSection
        v-if="activeSection === 'scores'"
        :is-admin="isAdmin"
        :rows="visibleScoreBoardRows"
        @open-import="openScoreImport"
        @refresh="refreshScoreBoard"
        @edit-score="openScoreEditByBoard"
      />

      <AdmissionsSection
        v-if="activeSection === 'admissions'"
        :rows="visibleAdmissionBoardRows"
        :can-operate="canAdmissionOperate"
        @refresh="refreshAdmissionBoard"
        @action="applyAdmissionAction"
      />

      <section v-if="activeSection === 'notices'" class="card">
        <SectionHeader title="公告管理表格">
          <template #actions>
            <button v-if="isAdmin" class="btn primary" @click="openNoticeCreate">新增公告</button>
            <button class="btn ghost small" @click="loadNotices">刷新</button>
          </template>
        </SectionHeader>
        <table class="table">
          <thead><tr><th>ID</th><th>标题</th><th>内容预览</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="n in notices" :key="n.id">
              <td>{{ n.id }}</td><td>{{ n.title }}</td><td>{{ previewText(n.content) }}</td>
              <td><button v-if="isAdmin" class="btn ghost small" @click="openNoticeEdit(n)">编辑</button></td>
            </tr>
          </tbody>
        </table>
      </section>
    </main>
  </div>

  <div v-if="modal.open" class="modal-mask" @click.self="closeModal">
    <div class="modal-card">
      <div class="card-head">
        <h3>{{ modal.title }}</h3>
        <button class="btn ghost small" @click="closeModal">关闭</button>
      </div>

      <template v-if="modal.type === 'profile'">
        <p><b>姓名：</b>{{ modal.form.name }}</p>
        <p><b>准考证：</b>{{ modal.form.exam_no }}</p>
        <p><b>身份证：</b>{{ modal.form.id_card }}</p>
        <p><b>电话：</b>{{ modal.form.phone }}</p>
      </template>

      <template v-if="modal.type === 'profile_manage'">
        <div class="tab-switch">
          <button class="tab-btn" :class="{ active: profileCreateTab === 'manual' }" @click="profileCreateTab = 'manual'">单个新增</button>
          <button class="tab-btn" :class="{ active: profileCreateTab === 'excel' }" @click="profileCreateTab = 'excel'">Excel导入</button>
        </div>
        <template v-if="profileCreateTab === 'manual'">
          <label><span>登录账号</span><input v-model="modal.form.username" /></label>
          <label><span>登录密码</span><input v-model="modal.form.password" /></label>
          <label><span>准考证号</span><input v-model="modal.form.exam_no" /></label>
          <label><span>姓名</span><input v-model="modal.form.name" /></label>
          <label><span>身份证号</span><input v-model="modal.form.id_card" /></label>
          <label><span>手机号</span><input v-model="modal.form.phone" /></label>
        </template>
        <template v-else>
          <div class="import-box">
            <label><span>Excel 文件（.xlsx）</span></label>
            <div class="file-picker">
              <input id="profile-import-file" class="file-input-hidden" type="file" accept=".xlsx" @change="onProfileFileChange" />
              <label class="file-btn" for="profile-import-file">选择文件</label>
              <span class="file-name">{{ profileImportName }}</span>
            </div>
            <p class="muted">模板列顺序：username, password, exam_no, name, id_card, phone</p>
            <button class="btn primary" @click="importProfilesFromModal">执行导入</button>
          </div>
        </template>
      </template>

      <template v-if="modal.type === 'profile_edit'">
        <label><span>准考证号</span><input v-model="modal.form.exam_no" /></label>
        <label><span>姓名</span><input v-model="modal.form.name" /></label>
        <label><span>身份证号</span><input v-model="modal.form.id_card" /></label>
        <label><span>手机号</span><input v-model="modal.form.phone" /></label>
      </template>

      <template v-if="modal.type === 'my_profile_edit'">
        <label><span>准考证号</span><input v-model="modal.form.exam_no" /></label>
        <label><span>姓名</span><input v-model="modal.form.name" /></label>
        <label><span>身份证号</span><input v-model="modal.form.id_card" /></label>
        <label><span>手机号</span><input v-model="modal.form.phone" /></label>
      </template>

      <template v-if="modal.type === 'choice'">
        <label><span>考生ID</span><input v-model.number="modal.form.candidate_id" readonly /></label>
        <p class="muted">考生姓名：{{ candidateName(modal.form.candidate_id) }}</p>
        <label>
          <span>批次</span>
          <select v-model="modal.form.batch">
            <option v-for="item in batchOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label>
          <span>院校</span>
          <select v-model="modal.form.university" @change="onChoiceUniversityChange">
            <option v-for="item in universityOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label>
          <span>专业</span>
          <select v-model="modal.form.major">
            <option v-for="item in choiceMajorOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label>
          <span>优先级</span>
          <select v-model.number="modal.form.priority">
            <option v-for="item in priorityOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
      </template>

      <template v-if="modal.type === 'score'">
        <label><span>考生ID</span><input v-model.number="modal.form.candidate_id" /></label>
        <p class="muted">考生姓名：{{ candidateName(modal.form.candidate_id) }}</p>
        <label><span>语文</span><input v-model.number="modal.form.chinese" /></label>
        <label><span>数学</span><input v-model.number="modal.form.math" /></label>
        <label><span>外语</span><input v-model.number="modal.form.foreign_language" /></label>
        <label><span>综合</span><input v-model.number="modal.form.comprehensive" /></label>
      </template>

      <template v-if="modal.type === 'score_import'">
        <div class="import-box">
          <label><span>Excel 文件（.xlsx）</span></label>
          <div class="file-picker">
            <input id="score-import-file" class="file-input-hidden" type="file" accept=".xlsx" @change="onScoreFileChange" />
            <label class="file-btn" for="score-import-file">选择文件</label>
            <span class="file-name">{{ scoreImportName }}</span>
          </div>
          <div class="toolbar-inline">
            <button class="btn ghost small" @click="downloadScoreTemplate">导出模板</button>
          </div>
          <p class="muted">先导出模板（包含全部考生），填完四科后再导入。</p>
          <p class="muted">模板列顺序：candidate_id, name, exam_no, 语文, 数学, 外语, 综合</p>
          <button class="btn primary" @click="importScoresFromModal">执行导入</button>
        </div>
      </template>

      <template v-if="modal.type === 'admission'">
        <label><span>考生ID</span><input v-model.number="modal.form.candidate_id" /></label>
        <p class="muted">考生姓名：{{ candidateName(modal.form.candidate_id) }}</p>
        <label><span>院校</span><input v-model="modal.form.university" /></label>
        <label><span>专业</span><input v-model="modal.form.major" /></label>
        <label>
          <span>状态</span>
          <select v-model="modal.form.status">
            <option value="admitted">录取</option>
            <option value="pending">拟录取</option>
            <option value="rejected">拒绝</option>
          </select>
        </label>
      </template>

      <template v-if="modal.type === 'notice'">
        <label><span>标题</span><input v-model="modal.form.title" /></label>
        <label><span>内容（未过滤）</span><textarea v-model="modal.form.content"></textarea></label>
      </template>

      <div
        class="toolbar"
        v-if="modal.type !== 'profile' && !(modal.type === 'profile_manage' && profileCreateTab === 'excel') && modal.type !== 'score_import'"
      >
        <button class="btn primary" @click="saveModal">保存</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import SectionHeader from '../components/SectionHeader.vue'
import ScoresSection from '../components/ScoresSection.vue'
import AdmissionsSection from '../components/AdmissionsSection.vue'
import OverviewCharts from '../components/OverviewCharts.vue'

const API_BASE = 'http://127.0.0.1:8000'
const router = useRouter()

const user = ref(null)
const actionMsg = ref('')
const activeSection = ref('overview')

const navItems = [
  { key: 'overview', label: '系统总览', desc: '系统数据概览与入口引导' },
  { key: 'profiles', label: '考生信息', desc: '考生表格与详情弹窗' },
  { key: 'scores', label: '成绩录入', desc: '成绩表格、手工录入与Excel导入' },
  { key: 'choices', label: '志愿填报', desc: '志愿表格与新增/编辑弹窗' },
  { key: 'admissions', label: '录取管理', desc: '录取表格与新增/编辑弹窗' },
  { key: 'notices', label: '公告管理', desc: '公告表格与新增/编辑弹窗' }
]
const candidateNavItems = [
  { key: 'profiles', label: '我的信息', desc: '个人档案查看' },
  { key: 'scores', label: '我的成绩', desc: '个人成绩查看' },
  { key: 'choices', label: '我的志愿', desc: '个人志愿查看' },
  { key: 'admissions', label: '我的录取', desc: '个人录取结果查看' },
  { key: 'notices', label: '公告', desc: '公告查看' }
]
const batchOptions = ['本科提前批', '本科一批', '本科二批', '高职高专']
const priorityOptions = [1, 2, 3]
const universityOptions = ['示例大学', '东海理工大学', '江城大学', '华北学院', '南方科技学院']
const majorOptionsMap = {
  示例大学: ['计算机科学', '软件工程', '人工智能'],
  东海理工大学: ['软件工程', '网络工程', '信息管理'],
  江城大学: ['信息安全', '电子信息', '自动化'],
  华北学院: ['网络工程', '通信工程', '数据科学'],
  南方科技学院: ['数据科学', '智能制造', '数字媒体']
}

const isCandidate = computed(() => user.value?.role === 'candidate')
const isAdmin = computed(() => !isCandidate.value)
const canAdmissionOperate = computed(() => isAdmin.value)
const visibleNavItems = computed(() => (isAdmin.value ? navItems : candidateNavItems))
const current = computed(() => visibleNavItems.value.find((i) => i.key === activeSection.value) || visibleNavItems.value[0])
const currentTitle = computed(() => current.value.label)
const currentDesc = computed(() => current.value.desc)
const currentCandidateProfileId = computed(() => {
  const p = profiles.value.find((x) => user.value && x.user_id === user.value.id)
  return p ? p.id : null
})
const visibleProfiles = computed(() =>
  isAdmin.value ? profiles.value : profiles.value.filter((p) => user.value && p.user_id === user.value.id)
)
const visibleChoices = computed(() =>
  isAdmin.value
    ? choices.value
    : choices.value.filter((c) => currentCandidateProfileId.value && c.candidate_id === currentCandidateProfileId.value)
)
const candidateAdmissionLocked = computed(() => {
  if (isAdmin.value || !currentCandidateProfileId.value) return false
  const myAdmission = admissions.value
    .filter((a) => a.candidate_id === currentCandidateProfileId.value)
    .sort((a, b) => b.id - a.id)
  if (!myAdmission.length) return false
  return myAdmission[0].status === 'admitted'
})
const candidateHasScore = computed(() => {
  if (isAdmin.value || !currentCandidateProfileId.value) return true
  const row = scoreBoardRows.value.find((r) => r.candidate_id === currentCandidateProfileId.value)
  return !!row?.has_score
})
const candidateChoiceLocked = computed(() => candidateAdmissionLocked.value || !candidateHasScore.value)
const candidateChoiceLockReason = computed(() => {
  if (!candidateChoiceLocked.value) return ''
  if (!candidateHasScore.value) return '未出成绩，暂不可填报志愿'
  if (candidateAdmissionLocked.value) return '已录取后不可填报或编辑志愿'
  return ''
})
const visibleScoreBoardRows = computed(() =>
  isAdmin.value
    ? scoreBoardRows.value
    : scoreBoardRows.value.filter((r) => currentCandidateProfileId.value && r.candidate_id === currentCandidateProfileId.value)
)
const scoredCandidateCount = computed(() => scoreBoardRows.value.filter((r) => r.has_score).length)
const visibleAdmissionBoardRows = computed(() =>
  isAdmin.value
    ? admissionBoard.value
    : admissionBoard.value.filter((r) => currentCandidateProfileId.value && r.candidate_id === currentCandidateProfileId.value)
)
const admissionStats = computed(() => {
  const base = { admitted: 0, pending: 0, rejected: 0, none: 0 }
  for (const r of visibleAdmissionBoardRows.value) {
    if (r.status === 'admitted') base.admitted += 1
    else if (r.status === 'pending') base.pending += 1
    else if (r.status === 'rejected') base.rejected += 1
    else base.none += 1
  }
  return base
})
const scoreBuckets = computed(() => {
  const buckets = [0, 0, 0, 0]
  for (const r of visibleScoreBoardRows.value) {
    const v = Number(r.total_score || 0)
    if (v < 450) buckets[0] += 1
    else if (v < 550) buckets[1] += 1
    else if (v < 650) buckets[2] += 1
    else buckets[3] += 1
  }
  return buckets
})
const choiceMajorOptions = computed(() => {
  const uni = modal.form?.university
  const options = majorOptionsMap[uni]
  if (options && options.length) {
    return options
  }
  return ['计算机科学', '软件工程', '信息安全']
})
const scoreBoardRows = computed(() => {
  const latestByCandidateSubject = {}
  for (const s of scores.value) {
    const key = `${s.candidate_id}_${s.subject}`
    const old = latestByCandidateSubject[key]
    if (!old || s.id > old.id) {
      latestByCandidateSubject[key] = s
    }
  }
  return profiles.value.map((p) => {
    const chinese = Number((latestByCandidateSubject[`${p.id}_语文`]?.score) || 0)
    const math = Number((latestByCandidateSubject[`${p.id}_数学`]?.score) || 0)
    const foreignLanguage = Number((latestByCandidateSubject[`${p.id}_外语`]?.score) || 0)
    const comprehensive = Number((latestByCandidateSubject[`${p.id}_综合`]?.score) || 0)
    const totalScore = chinese + math + foreignLanguage + comprehensive
    return {
      candidate_id: p.id,
      name: p.name,
      exam_no: p.exam_no,
      chinese,
      math,
      foreign_language: foreignLanguage,
      comprehensive,
      total_score: totalScore,
      has_score: totalScore > 0
    }
  })
})

const profiles = ref([])
const choices = ref([])
const scores = ref([])
const admissions = ref([])
const admissionBoard = ref([])
const notices = ref([])
const scoreImportFile = ref(null)
const scoreCreateTab = ref('manual')
const profileImportFile = ref(null)
const profileCreateTab = ref('manual')
const scoreImportName = ref('未选择文件')
const profileImportName = ref('未选择文件')

const modal = reactive({
  open: false,
  type: '',
  mode: 'create',
  title: '',
  id: null,
  form: {}
})

function authHeaders(withJson = false) {
  const headers = {}
  if (withJson) headers['Content-Type'] = 'application/json'
  if (user.value?.token) headers.Authorization = `Bearer ${user.value.token}`
  return headers
}

async function readError(res) {
  try {
    const data = await res.json()
    return data.detail || JSON.stringify(data)
  } catch {
    return await res.text()
  }
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders()
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

async function apiPost(path, payload) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: authHeaders(true),
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

async function apiPut(path, payload) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: authHeaders(true),
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

async function apiPostForm(path, formData) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: authHeaders(),
    body: formData
  })
  if (!res.ok) throw new Error(await readError(res))
  return res.json()
}

function setAction(text) {
  actionMsg.value = text
  setTimeout(() => {
    if (actionMsg.value === text) actionMsg.value = ''
  }, 2200)
}

function candidateName(candidateId) {
  const p = profiles.value.find((x) => x.id === Number(candidateId))
  return p ? p.name : '未找到'
}

function closeModal() {
  modal.open = false
}

function openProfileModal(p) {
  modal.open = true
  modal.type = 'profile'
  modal.mode = 'view'
  modal.id = p.id
  modal.title = '考生详情'
  modal.form = { ...p }
}

function openProfileCreate() {
  modal.open = true
  modal.type = 'profile_manage'
  modal.mode = 'create'
  modal.id = null
  modal.title = '新增/导入考生'
  profileCreateTab.value = 'manual'
  profileImportFile.value = null
  profileImportName.value = '未选择文件'
  modal.form = { username: '', password: '123456', exam_no: '', name: '', id_card: '', phone: '' }
}

function openProfileEdit(p) {
  modal.open = true
  modal.type = 'profile_edit'
  modal.mode = 'edit'
  modal.id = p.id
  modal.title = '编辑考生'
  modal.form = {
    exam_no: p.exam_no,
    name: p.name,
    id_card: p.id_card,
    phone: p.phone
  }
}

async function openMyProfileEdit() {
  try {
    const meProfile = await apiGet('/api/me/profile')
    modal.open = true
    modal.type = 'my_profile_edit'
    modal.mode = 'edit'
    modal.id = meProfile.id
    modal.title = '编辑个人信息'
    modal.form = {
      exam_no: meProfile.exam_no,
      name: meProfile.name,
      id_card: meProfile.id_card,
      phone: meProfile.phone
    }
  } catch (e) {
    setAction('当前账号没有可编辑的个人档案')
  }
}

function openChoiceCreate() {
  if (!candidateHasScore.value) {
    setAction('未出成绩，暂不可填报志愿')
    return
  }
  if (candidateAdmissionLocked.value) {
    setAction('已录取后不可新增志愿')
    return
  }
  const cid = currentCandidateProfileId.value || 1
  const myChoiceCount = choices.value.filter((c) => c.candidate_id === cid).length
  if (myChoiceCount >= 3) {
    setAction('你已填报 3 个志愿，不能继续新增')
    return
  }
  modal.open = true
  modal.type = 'choice'
  modal.mode = 'create'
  modal.id = null
  modal.title = '新增志愿'
  modal.form = {
    candidate_id: cid,
    batch: '本科一批',
    university: universityOptions[0],
    major: majorOptionsMap[universityOptions[0]][0],
    priority: getNextPriorityForCandidate(cid)
  }
}

function openChoiceEdit(row) {
  if (!candidateHasScore.value) {
    setAction('未出成绩，暂不可编辑志愿')
    return
  }
  if (candidateAdmissionLocked.value) {
    setAction('已录取后不可编辑志愿')
    return
  }
  modal.open = true
  modal.type = 'choice'
  modal.mode = 'edit'
  modal.id = row.id
  modal.title = '编辑志愿'
  modal.form = { ...row }
  onChoiceUniversityChange()
}

function onChoiceUniversityChange() {
  const options = majorOptionsMap[modal.form.university] || []
  if (!options.includes(modal.form.major)) {
    modal.form.major = options[0] || ''
  }
}

function getNextPriorityForCandidate(candidateId) {
  const used = new Set(
    choices.value.filter((c) => c.candidate_id === candidateId).map((c) => Number(c.priority))
  )
  for (const p of priorityOptions) {
    if (!used.has(p)) {
      return p
    }
  }
  return 1
}

function openScoreCreate() {
  modal.open = true
  modal.type = 'score'
  modal.mode = 'create'
  modal.id = null
  modal.title = '新增成绩'
  scoreCreateTab.value = 'manual'
  scoreImportFile.value = null
  scoreImportName.value = '未选择文件'
  modal.form = { candidate_id: 1, chinese: 0, math: 0, foreign_language: 0, comprehensive: 0 }
}

function openScoreCreateForCandidate(row) {
  modal.open = true
  modal.type = 'score'
  modal.mode = 'create'
  modal.id = null
  modal.title = `为 ${row.name} 新增成绩`
  scoreCreateTab.value = 'manual'
  scoreImportFile.value = null
  scoreImportName.value = '未选择文件'
  modal.form = {
    candidate_id: row.candidate_id,
    chinese: row.chinese || 0,
    math: row.math || 0,
    foreign_language: row.foreign_language || 0,
    comprehensive: row.comprehensive || 0
  }
}

function openScoreEdit(row) {
  modal.open = true
  modal.type = 'score'
  modal.mode = 'edit'
  modal.id = row.id
  modal.title = '编辑成绩'
  scoreCreateTab.value = 'manual'
  modal.form = { ...row }
}

function openScoreEditByBoard(row) {
  modal.open = true
  modal.type = 'score'
  modal.mode = 'edit'
  modal.id = row.candidate_id
  modal.title = `编辑 ${row.name} 四科成绩`
  scoreCreateTab.value = 'manual'
  modal.form = {
    candidate_id: row.candidate_id,
    chinese: row.chinese || 0,
    math: row.math || 0,
    foreign_language: row.foreign_language || 0,
    comprehensive: row.comprehensive || 0
  }
}

function openScoreImport() {
  modal.open = true
  modal.type = 'score_import'
  modal.mode = 'import'
  modal.id = null
  modal.title = '成绩导入'
  scoreImportFile.value = null
  scoreImportName.value = '未选择文件'
  modal.form = {}
}

function openAdmissionCreate() {
  modal.open = true
  modal.type = 'admission'
  modal.mode = 'create'
  modal.id = null
  modal.title = '新增录取'
  modal.form = { candidate_id: 1, university: '', major: '', status: 'admitted' }
}

function openAdmissionCreateForCandidate(row) {
  modal.open = true
  modal.type = 'admission'
  modal.mode = 'create'
  modal.id = null
  modal.title = `为 ${row.name} 新增录取`
  modal.form = { candidate_id: row.candidate_id, university: '', major: '', status: 'admitted' }
}

async function applyAdmissionAction(row, status, label, selectedChoice = null) {
  const existed = row.admission_id ? { id: row.admission_id } : null
  const university =
    (selectedChoice && selectedChoice.university) ||
    row.university ||
    row.choice_university ||
    ''
  const major =
    (selectedChoice && selectedChoice.major) ||
    row.major ||
    row.choice_major ||
    ''
  if (!university || !major) {
    setAction('该考生未填报志愿，无法录取操作')
    return
  }

  const payload = {
    candidate_id: row.candidate_id,
    university,
    major,
    status
  }
  if (existed) {
    await apiPut(`/api/admissions/${existed.id}`, payload)
  } else {
    await apiPost('/api/admissions', payload)
  }
  await loadAdmissions()
  await loadAdmissionBoard()
  setAction(`${label}操作成功`)
}

function goAdmissionFromChoice(choiceRow) {
  activeSection.value = 'admissions'
  const row = admissionBoard.value.find((x) => x.candidate_id === choiceRow.candidate_id)
  if (!row) {
    return
  }
  applyAdmissionAction(row, 'admitted', '录取')
}

function openAdmissionEdit(row) {
  modal.open = true
  modal.type = 'admission'
  modal.mode = 'edit'
  modal.id = row.id
  modal.title = '编辑录取'
  modal.form = { ...row }
}

function openAdmissionEditByBoard(row) {
  openAdmissionEdit({
    id: row.admission_id,
    candidate_id: row.candidate_id,
    university: row.university || '',
    major: row.major || '',
    status: row.status || 'pending'
  })
}

function openNoticeCreate() {
  modal.open = true
  modal.type = 'notice'
  modal.mode = 'create'
  modal.id = null
  modal.title = '新增公告'
  modal.form = { title: '', content: '' }
}

function openNoticeEdit(row) {
  modal.open = true
  modal.type = 'notice'
  modal.mode = 'edit'
  modal.id = row.id
  modal.title = '编辑公告'
  modal.form = { ...row }
}

async function saveModal() {
  if (modal.type === 'profile_manage') {
    await apiPost('/api/profiles', modal.form)
    await loadProfiles()
    setAction('考生新增成功')
  }
  if (modal.type === 'profile_edit') {
    await apiPut(`/api/profiles/${modal.id}`, modal.form)
    await loadProfiles()
    setAction('考生信息已更新')
  }
  if (modal.type === 'my_profile_edit') {
    await apiPut('/api/me/profile', modal.form)
    await loadProfiles()
    setAction('个人信息已更新')
  }
  if (modal.type === 'choice') {
    if (modal.mode === 'create') await apiPost('/api/choices', modal.form)
    else await apiPut(`/api/choices/${modal.id}`, modal.form)
    await loadChoices()
    setAction('志愿保存成功')
  }
  if (modal.type === 'score') {
    await apiPost('/api/scores/batch', modal.form)
    await loadScores()
    setAction('成绩保存成功')
  }
  if (modal.type === 'admission') {
    if (modal.mode === 'create') await apiPost('/api/admissions', modal.form)
    else await apiPut(`/api/admissions/${modal.id}`, modal.form)
    await loadAdmissions()
    setAction('录取保存成功')
  }
  if (modal.type === 'notice') {
    if (modal.mode === 'create') await apiPost('/api/notices', modal.form)
    else await apiPut(`/api/notices/${modal.id}`, modal.form)
    await loadNotices()
    setAction('公告保存成功')
  }
  closeModal()
}

function onProfileFileChange(event) {
  const file = event.target.files && event.target.files[0]
  profileImportFile.value = file || null
  profileImportName.value = file ? file.name : '未选择文件'
}

async function importProfilesFromModal() {
  if (!profileImportFile.value) {
    setAction('请先选择 .xlsx 文件')
    return
  }
  const formData = new FormData()
  formData.append('file', profileImportFile.value)
  const result = await apiPostForm('/api/profiles/import', formData)
  await loadProfiles()
  setAction(`导入完成，共 ${result.imported} 条`)
  closeModal()
}

function onScoreFileChange(event) {
  const file = event.target.files && event.target.files[0]
  scoreImportFile.value = file || null
  scoreImportName.value = file ? file.name : '未选择文件'
}

async function importScores() {
  if (!scoreImportFile.value) {
    setAction('请先选择 .xlsx 文件')
    return
  }
  const formData = new FormData()
  formData.append('file', scoreImportFile.value)
  const result = await apiPostForm('/api/scores/import-template', formData)
  await loadScores()
  setAction(`导入完成，共 ${result.imported} 条`)
}

async function downloadScoreTemplate() {
  const res = await fetch(`${API_BASE}/api/scores/template`, {
    headers: authHeaders()
  })
  if (!res.ok) throw new Error(await readError(res))
  const blob = await res.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'scores_template.xlsx'
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
  setAction('模板已导出')
}

async function importScoresFromModal() {
  await importScores()
  closeModal()
}

function previewText(text) {
  if (!text) return ''
  return text.length > 28 ? `${text.slice(0, 28)}...` : text
}

function logout() {
  user.value = null
  localStorage.removeItem('admission_user')
  activeSection.value = 'overview'
  router.replace('/login')
}

async function loadProfiles() { profiles.value = await apiGet('/api/profiles') }
async function loadChoices() { choices.value = await apiGet('/api/choices') }
async function loadScores() { scores.value = await apiGet('/api/scores') }
async function loadAdmissions() { admissions.value = await apiGet('/api/admissions') }
async function loadAdmissionBoard() { admissionBoard.value = await apiGet('/api/admission-board') }
async function loadNotices() { notices.value = await apiGet('/api/notices') }
async function refreshScoreBoard() { await Promise.all([loadProfiles(), loadScores()]) }
async function refreshAdmissionBoard() { await Promise.all([loadProfiles(), loadAdmissions(), loadAdmissionBoard()]) }

async function loadAll() {
  await Promise.all([loadProfiles(), loadChoices(), loadScores(), loadAdmissions(), loadAdmissionBoard(), loadNotices()])
}

onMounted(async () => {
  const cache = localStorage.getItem('admission_user')
  if (!cache) {
    router.replace('/login')
    return
  }
  user.value = JSON.parse(cache)
  if (!user.value?.token) {
    user.value = null
    localStorage.removeItem('admission_user')
    router.replace('/login')
    return
  }
  try {
    await loadAll()
    if (!visibleNavItems.value.find((i) => i.key === activeSection.value)) {
      activeSection.value = visibleNavItems.value[0].key
    }
  } catch {
    user.value = null
    localStorage.removeItem('admission_user')
    router.replace('/login')
  }
})

watch(activeSection, async (section) => {
  if (section === 'admissions') {
    await refreshAdmissionBoard()
  }
})
</script>
