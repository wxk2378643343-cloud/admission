<script setup>
import { onMounted, reactive, ref } from 'vue'
import { request } from '../../api'

const keyword = ref('')
const pageData = ref({ items: [], page: 1, page_count: 1, total: 0 })
const choices = ref([])
const selected = ref(null)
const showModal = ref(false)
const error = ref('')
const form = reactive({
  choice_id: '',
  result: '待定',
  publish_status: '未发布'
})

function isLocked(row) {
  return row.publish_status === '已发布' && row.admission_result !== '待定'
}

async function loadData(page = 1) {
  pageData.value = await request(
    `/admin/admission-review?keyword=${encodeURIComponent(keyword.value)}&page=${page}&page_size=8`
  )
}

async function openReview(row) {
  error.value = ''
  selected.value = row
  choices.value = await request(`/admin/students/${row.student_id}/choices`)
  form.choice_id = row.choice_id || choices.value[0]?.id || ''
  form.result = row.admission_result || '待定'
  form.publish_status = row.publish_status || '未发布'
  showModal.value = true
}

async function submitReview() {
  error.value = ''
  const result = await request('/admin/admission-review', {
    method: 'POST',
    body: JSON.stringify({
      student_id: selected.value.student_id,
      choice_id: form.choice_id ? Number(form.choice_id) : null,
      result: form.result,
      publish_status: form.publish_status
    })
  })
  if (!result.success) {
    error.value = result.message
    return
  }
  showModal.value = false
  await loadData(pageData.value.page)
}

onMounted(loadData)
</script>

<template>
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="eyebrow">Admission Review</div>
        <h3>录取分配</h3>
      </div>
      <span class="count-pill">共 {{ pageData.total }} 名学生</span>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <input v-model="keyword" class="input" placeholder="按姓名、学号或专业查询" />
        <button class="btn" @click="loadData()">查询</button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>学号</th>
            <th>姓名</th>
            <th>成绩</th>
            <th>当前状态</th>
            <th>志愿数</th>
            <th>录取结果</th>
            <th>录取专业</th>
            <th>发布状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in pageData.items" :key="row.student_id">
            <td>{{ row.student_no }}</td>
            <td>{{ row.name }}</td>
            <td><strong>{{ row.score }}</strong></td>
            <td>{{ row.status }}</td>
            <td>{{ row.choice_count }}</td>
            <td>{{ row.admission_result || '未处理' }}</td>
            <td>{{ row.admitted_major || row.major || '暂未确定' }}</td>
            <td>{{ row.publish_status || '未发布' }}</td>
            <td>
              <button
                class="btn small"
                :disabled="isLocked(row)"
                @click="openReview(row)"
              >
                {{ isLocked(row) ? '已完成' : '处理录取' }}
              </button>
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
          <div class="eyebrow">Review Form</div>
          <h3>{{ selected?.name }} 的录取处理</h3>
        </div>
        <button class="ghost-close" @click="showModal = false">×</button>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
      <div class="review-summary">
        <span>学号：{{ selected?.student_no }}</span>
        <span>成绩：{{ selected?.score }}</span>
        <span>状态：{{ selected?.status }}</span>
      </div>

      <div class="field">
        <label>录取结果</label>
        <select v-model="form.result" class="input">
          <option>录取</option>
          <option>未录取</option>
          <option>待定</option>
        </select>
      </div>

      <div class="field" v-if="form.result === '录取'">
        <label>选择录取志愿</label>
        <select v-model="form.choice_id" class="input">
          <option value="">请选择志愿</option>
          <option v-for="choice in choices" :key="choice.id" :value="choice.id">
            第 {{ choice.choice_order }} 志愿 / {{ choice.batch }} / {{ choice.college }} / {{ choice.major }}
          </option>
        </select>
      </div>

      <div class="choice-list compact-list" v-if="choices.length">
        <div v-for="choice in choices" :key="choice.id" class="choice-item">
          <strong>第 {{ choice.choice_order }} 志愿</strong>
          <span>{{ choice.batch }} / {{ choice.college }} / {{ choice.major }}</span>
          <em>{{ choice.status }}</em>
        </div>
      </div>
      <div v-else class="empty-state">该学生暂未填报志愿，不能选择志愿录取。</div>

      <div class="field">
        <label>发布状态</label>
        <select v-model="form.publish_status" class="input">
          <option>未发布</option>
          <option>已发布</option>
        </select>
      </div>

      <div class="modal-actions">
        <button class="btn secondary" @click="showModal = false">取消</button>
        <button class="btn" @click="submitReview">保存结果</button>
      </div>
    </div>
  </div>
</template>
