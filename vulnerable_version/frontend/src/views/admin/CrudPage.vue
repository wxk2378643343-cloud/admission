<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { request } from '../../api'

const route = useRoute()
const keyword = ref('')
const pageData = ref({ items: [], page: 1, page_count: 1, total: 0 })
const showModal = ref(false)
const showPasswordModal = ref(false)
const editingId = ref(null)
const formError = ref('')
const passwordTarget = ref(null)
const passwordForm = reactive({ new_password: '' })
const passwordMessage = ref('')
const passwordError = ref('')

const configMap = {
  students: {
    title: '学生信息管理',
    endpoint: '/admin/students',
    columns: [
      ['id', 'ID'],
      ['user_id', '用户ID'],
      ['student_no', '学号'],
      ['name', '姓名'],
      ['gender', '性别'],
      ['score', '成绩'],
      ['major', '专业'],
      ['status', '状态']
    ],
    form: {
      student_no: '',
      name: '',
      gender: ''
    },
    fields: [
      { key: 'student_no', label: '学号', type: 'text' },
      { key: 'name', label: '姓名', type: 'text' },
      { key: 'gender', label: '性别', type: 'select', options: ['男', '女'] }
    ]
  },
  plans: {
    title: '招生计划管理',
    endpoint: '/admin/plans',
    columns: [
      ['id', 'ID'],
      ['year', '年份'],
      ['batch', '批次'],
      ['college', '学院'],
      ['major', '专业'],
      ['quota', '人数']
    ],
    form: { year: 2026, batch: '', college: '', major: '', quota: '' },
    fields: [
      { key: 'year', label: '年份', type: 'select', options: [2025, 2026, 2027] },
      { key: 'batch', label: '批次', type: 'select', options: ['提前批', '本科一批', '本科二批', '专科批'] },
      { key: 'college', label: '学院', type: 'text' },
      { key: 'major', label: '专业', type: 'text' },
      { key: 'quota', label: '人数', type: 'number' }
    ]
  },
  admissions: {
    title: '录取信息管理',
    endpoint: '/admin/admissions',
    columns: [
      ['id', 'ID'],
      ['student_id', '学生ID'],
      ['student_name', '学生姓名'],
      ['batch', '批次'],
      ['major', '专业'],
      ['result', '结果'],
      ['publish_status', '发布状态']
    ],
    form: {
      student_id: '',
      student_name: '',
      batch: '',
      major: '',
      result: '',
      publish_status: ''
    },
    fields: [
      { key: 'student_id', label: '学生ID', type: 'number' },
      { key: 'student_name', label: '学生姓名', type: 'text' },
      { key: 'batch', label: '批次', type: 'select', options: ['提前批', '本科一批', '本科二批', '专科批'] },
      { key: 'major', label: '专业', type: 'text' },
      { key: 'result', label: '结果', type: 'select', options: ['待定', '录取', '未录取'] },
      { key: 'publish_status', label: '发布状态', type: 'select', options: ['未发布', '已发布'] }
    ]
  },
  notices: {
    title: '公告管理',
    endpoint: '/admin/notices',
    columns: [
      ['id', 'ID'],
      ['title', '标题'],
      ['publisher', '发布人'],
      ['created_at', '发布时间']
    ],
    form: { title: '', content: '', publisher: '', created_at: '' },
    fields: [
      { key: 'title', label: '标题', type: 'text' },
      { key: 'publisher', label: '发布人', type: 'select', options: ['招生办公室', '系统管理员'] },
      { key: 'created_at', label: '发布时间', type: 'text' },
      { key: 'content', label: '公告内容', type: 'textarea' }
    ]
  }
}

const current = computed(() => configMap[route.meta.resource])
const form = reactive({})

function resetForm() {
  Object.keys(form).forEach((key) => delete form[key])
  Object.assign(form, current.value.form)
}

async function loadData(page = 1) {
  pageData.value = await request(
    `${current.value.endpoint}?keyword=${encodeURIComponent(keyword.value)}&page=${page}&page_size=5`
  )
}

function openCreate() {
  editingId.value = null
  formError.value = ''
  resetForm()
  if (route.meta.resource === 'notices') {
    form.created_at = new Date().toLocaleString('zh-CN')
  }
  showModal.value = true
}

function openEdit(row) {
  editingId.value = row.id
  formError.value = ''
  resetForm()
  current.value.fields.forEach((field) => {
    form[field.key] = row[field.key]
  })
  showModal.value = true
}

async function submitForm() {
  const method = editingId.value ? 'PUT' : 'POST'
  const path = editingId.value
    ? `${current.value.endpoint}/${editingId.value}`
    : current.value.endpoint
  const payload = {}
  current.value.fields.forEach((field) => {
    payload[field.key] = form[field.key]
  })
  const result = await request(path, {
    method,
    body: JSON.stringify(payload)
  })
  if (result.success === false) {
    formError.value = result.message
    return
  }
  showModal.value = false
  await loadData(pageData.value.page)
}

async function removeRow(id) {
  await request(`${current.value.endpoint}/${id}`, { method: 'DELETE' })
  await loadData(pageData.value.page)
}

function openPasswordReset(row) {
  passwordTarget.value = row
  passwordForm.new_password = ''
  passwordMessage.value = ''
  passwordError.value = ''
  showPasswordModal.value = true
}

async function submitPasswordReset() {
  passwordError.value = ''
  passwordMessage.value = ''
  const result = await request('/admin/reset-password', {
    method: 'POST',
    body: JSON.stringify({
      user_id: passwordTarget.value.user_id,
      new_password: passwordForm.new_password
    })
  })
  if (!result.success) {
    passwordError.value = result.message
    return
  }
  passwordMessage.value = result.message
}

watch(
  () => route.meta.resource,
  () => {
    resetForm()
    loadData()
  }
)

onMounted(() => {
  resetForm()
  loadData()
})
</script>

<template>
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="eyebrow">Data Management</div>
        <h3>{{ current.title }}</h3>
      </div>
      <span class="count-pill">共 {{ pageData.total }} 条</span>
    </div>
    <div class="toolbar">
      <div class="toolbar-left">
        <input v-model="keyword" class="input" :placeholder="`按关键字查询${current.title}`" />
        <button class="btn" @click="loadData()">查询</button>
      </div>
      <button class="btn" @click="openCreate">新增</button>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th v-for="column in current.columns" :key="column[0]">{{ column[1] }}</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in pageData.items" :key="row.id">
            <td v-for="column in current.columns" :key="column[0]">{{ row[column[0]] }}</td>
            <td>
              <div class="actions">
                <button class="btn small" @click="openEdit(row)">编辑</button>
                <button
                  v-if="route.meta.resource === 'students'"
                  class="btn secondary small"
                  :disabled="!row.user_id"
                  @click="openPasswordReset(row)"
                >
                  重置密码
                </button>
                <button class="btn secondary small" @click="removeRow(row.id)">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pager">
      <span>第 {{ pageData.page }} / {{ pageData.page_count }} 页</span>
      <button class="btn secondary" :disabled="pageData.page <= 1" @click="loadData(pageData.page - 1)">上一页</button>
      <button class="btn secondary" :disabled="pageData.page >= pageData.page_count" @click="loadData(pageData.page + 1)">下一页</button>
    </div>
  </div>

  <div v-if="showModal" class="modal-mask">
    <div class="modal-card">
      <div class="modal-head">
        <div>
          <div class="eyebrow">Record Form</div>
          <h3>{{ editingId ? '编辑' : '新增' }}{{ current.title }}</h3>
        </div>
        <button class="ghost-close" @click="showModal = false">×</button>
      </div>
      <div v-if="formError" class="error">{{ formError }}</div>
      <div class="form-grid">
        <div
          v-for="field in current.fields"
          :key="field.key"
          :class="{ full: field.type === 'textarea' }"
        >
          <label>{{ field.label }}</label>
          <textarea
            v-if="field.type === 'textarea'"
            v-model="form[field.key]"
            class="input"
            rows="5"
          />
          <select
            v-else-if="field.type === 'select'"
            v-model="form[field.key]"
            class="input"
          >
            <option value="">请选择{{ field.label }}</option>
            <option v-for="option in field.options" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
          <input
            v-else
            v-model="form[field.key]"
            class="input"
            :type="field.type"
          />
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn secondary" @click="showModal = false">取消</button>
        <button class="btn" @click="submitForm">保存</button>
      </div>
    </div>
  </div>

  <div v-if="showPasswordModal" class="modal-mask">
    <div class="modal-card account-modal">
      <div class="modal-head">
        <div>
          <div class="eyebrow">Password Reset</div>
          <h3>重置 {{ passwordTarget?.name }} 的密码</h3>
        </div>
        <button class="ghost-close" @click="showPasswordModal = false">×</button>
      </div>
      <div v-if="passwordError" class="error">{{ passwordError }}</div>
      <div v-if="passwordMessage" class="success">{{ passwordMessage }}</div>
      <div class="field">
        <label>用户ID</label>
        <input :value="passwordTarget?.user_id" class="input" disabled />
      </div>
      <div class="field">
        <label>新密码</label>
        <input v-model="passwordForm.new_password" class="input" type="password" placeholder="请输入新密码" />
      </div>
      <div class="modal-actions">
        <button class="btn secondary" @click="showPasswordModal = false">取消</button>
        <button class="btn" @click="submitPasswordReset">确认重置</button>
      </div>
    </div>
  </div>
</template>
