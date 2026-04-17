<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { request } from '../../api'

const keyword = ref('')
const pageData = ref({ items: [], page: 1, page_count: 1, total: 0 })
const showModal = ref(false)
const editing = ref(null)
const form = reactive({
  chinese_score: 0,
  math_score: 0,
  foreign_score: 0,
  comprehensive_score: 0,
  status: '待录取'
})

const totalScore = computed(
  () =>
    Number(form.chinese_score || 0) +
    Number(form.math_score || 0) +
    Number(form.foreign_score || 0) +
    Number(form.comprehensive_score || 0)
)

async function loadData(page = 1) {
  pageData.value = await request(
    `/admin/scores?keyword=${encodeURIComponent(keyword.value)}&page=${page}&page_size=8`
  )
}

function openEdit(row) {
  editing.value = row
  form.chinese_score = row.chinese_score
  form.math_score = row.math_score
  form.foreign_score = row.foreign_score
  form.comprehensive_score = row.comprehensive_score
  form.status = row.status
  showModal.value = true
}

async function submitForm() {
  await request(`/admin/scores/${editing.value.id}`, {
    method: 'PUT',
    body: JSON.stringify(form)
  })
  showModal.value = false
  await loadData(pageData.value.page)
}

onMounted(loadData)
</script>

<template>
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="eyebrow">Score Management</div>
        <h3>学生成绩管理</h3>
      </div>
      <span class="count-pill">共 {{ pageData.total }} 条</span>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <input v-model="keyword" class="input" placeholder="按姓名或学号查询" />
        <button class="btn" @click="loadData()">查询</button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>排名</th>
            <th>学号</th>
            <th>姓名</th>
            <th>性别</th>
            <th>语文</th>
            <th>数学</th>
            <th>外语</th>
            <th>综合</th>
            <th>总分</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in pageData.items" :key="row.id">
            <td>{{ (pageData.page - 1) * pageData.page_size + index + 1 }}</td>
            <td>{{ row.student_no }}</td>
            <td>{{ row.name }}</td>
            <td>{{ row.gender }}</td>
            <td>{{ row.chinese_score }}</td>
            <td>{{ row.math_score }}</td>
            <td>{{ row.foreign_score }}</td>
            <td>{{ row.comprehensive_score }}</td>
            <td><strong>{{ row.score }}</strong></td>
            <td>{{ row.status }}</td>
            <td><button class="btn small" @click="openEdit(row)">录入/修改</button></td>
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
    <div class="modal-card account-modal">
      <div class="modal-head">
        <div>
          <div class="eyebrow">Score Form</div>
          <h3>{{ editing?.name }} 成绩录入</h3>
        </div>
        <button class="ghost-close" @click="showModal = false">×</button>
      </div>
      <div class="score-form-grid">
        <div class="field">
          <label>语文</label>
          <input v-model="form.chinese_score" class="input" type="number" min="0" max="150" />
        </div>
        <div class="field">
          <label>数学</label>
          <input v-model="form.math_score" class="input" type="number" min="0" max="150" />
        </div>
        <div class="field">
          <label>外语</label>
          <input v-model="form.foreign_score" class="input" type="number" min="0" max="150" />
        </div>
        <div class="field">
          <label>综合</label>
          <input v-model="form.comprehensive_score" class="input" type="number" min="0" max="300" />
        </div>
      </div>
      <div class="score-total-preview">
        <span>自动计算总分</span>
        <strong>{{ totalScore }}</strong>
      </div>
      <div class="field">
        <label>状态</label>
        <select v-model="form.status" class="input">
          <option>未审核</option>
          <option>待录取</option>
        </select>
      </div>
      <div class="modal-actions">
        <button class="btn secondary" @click="showModal = false">取消</button>
        <button class="btn" @click="submitForm">保存</button>
      </div>
    </div>
  </div>
</template>
