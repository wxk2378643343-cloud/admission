<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { request } from '../../api'

const plans = ref([])
const choices = ref([])
const student = ref(null)
const locked = ref(false)
const showModal = ref(false)
const editing = ref(null)
const error = ref('')
const form = reactive({ plan_id: '', choice_order: 1 })

const maxChoices = 5
const selectedPlan = computed(() => plans.value.find((item) => item.id === Number(form.plan_id)))

async function loadData() {
  plans.value = await request('/student/plans')
  const result = await request('/student/choices')
  student.value = result.student
  choices.value = result.items
  locked.value = result.locked
}

function openCreate() {
  error.value = ''
  editing.value = null
  form.plan_id = plans.value[0]?.id || ''
  form.choice_order = choices.value.length + 1
  showModal.value = true
}

function openEdit(row) {
  error.value = ''
  editing.value = row
  form.plan_id = row.plan_id
  form.choice_order = row.choice_order
  showModal.value = true
}

async function submitForm() {
  error.value = ''
  const path = editing.value ? `/student/choices/${editing.value.id}` : '/student/choices'
  const method = editing.value ? 'PUT' : 'POST'
  const result = await request(path, {
    method,
    body: JSON.stringify({
      plan_id: Number(form.plan_id),
      choice_order: Number(form.choice_order)
    })
  })
  if (!result.success) {
    error.value = result.message
    return
  }
  showModal.value = false
  await loadData()
}

async function removeChoice(row) {
  const result = await request(`/student/choices/${row.id}`, { method: 'DELETE' })
  if (!result.success) {
    error.value = result.message
    return
  }
  await loadData()
}

async function moveChoice(row, direction) {
  await request(`/student/choices/${row.id}/order?direction=${direction}`, {
    method: 'PUT'
  })
  await loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="student-card feature-card wide-card">
    <div class="card-title-row">
      <div>
        <div class="eyebrow">Major Choices</div>
        <h3>我的志愿</h3>
      </div>
      <button class="btn" :disabled="locked || choices.length >= maxChoices" @click="openCreate">
        新增志愿
      </button>
    </div>
    <p class="meta">
      最多可填报 {{ maxChoices }} 个志愿，已录取或未录取后不可修改。当前状态：{{ student?.status || '待同步' }}
    </p>
    <div v-if="locked" class="success">录取结果已确定，志愿已锁定。</div>
    <div v-if="error" class="error">{{ error }}</div>

    <div class="choice-list">
      <div v-for="choice in choices" :key="choice.id" class="choice-item">
        <strong>第 {{ choice.choice_order }} 志愿</strong>
        <span>{{ choice.batch }} / {{ choice.college }} / {{ choice.major }}</span>
        <em>{{ choice.status }}</em>
        <div class="choice-actions">
          <button class="btn secondary small" :disabled="locked || choice.choice_order === 1" @click="moveChoice(choice, 'up')">上移</button>
          <button class="btn secondary small" :disabled="locked || choice.choice_order === choices.length" @click="moveChoice(choice, 'down')">下移</button>
          <button class="btn small" :disabled="locked" @click="openEdit(choice)">编辑</button>
          <button class="btn secondary small" :disabled="locked" @click="removeChoice(choice)">删除</button>
        </div>
      </div>
      <div v-if="!choices.length" class="empty-state">暂未填报志愿，请从招生计划中选择专业。</div>
    </div>
  </div>

  <div v-if="showModal" class="modal-mask">
    <div class="modal-card">
      <div class="modal-head">
        <div>
          <div class="eyebrow">Choice Form</div>
          <h3>{{ editing ? '编辑志愿' : '新增志愿' }}</h3>
        </div>
        <button class="ghost-close" @click="showModal = false">×</button>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="field" v-if="!editing">
        <label>志愿顺序</label>
        <select v-model="form.choice_order" class="input">
          <option v-for="index in choices.length + 1" :key="index" :value="index">
            第 {{ index }} 志愿
          </option>
        </select>
      </div>
      <div class="field">
        <label>招生计划</label>
        <select v-model="form.plan_id" class="input">
          <option v-for="plan in plans" :key="plan.id" :value="plan.id">
            {{ plan.batch }} / {{ plan.college }} / {{ plan.major }} / 计划{{ plan.quota }}人
          </option>
        </select>
      </div>
      <div v-if="selectedPlan" class="plan-preview">
        <span>批次：{{ selectedPlan.batch }}</span>
        <span>学院：{{ selectedPlan.college }}</span>
        <span>专业：{{ selectedPlan.major }}</span>
        <span>计划人数：{{ selectedPlan.quota }}</span>
      </div>
      <div class="modal-actions">
        <button class="btn secondary" @click="showModal = false">取消</button>
        <button class="btn" @click="submitForm">保存</button>
      </div>
    </div>
  </div>
</template>
