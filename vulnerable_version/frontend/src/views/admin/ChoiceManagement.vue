<script setup>
import { onMounted, ref } from 'vue'
import { request } from '../../api'

const keyword = ref('')
const pageData = ref({ items: [], page: 1, page_count: 1, total: 0 })
const detail = ref([])
const selected = ref(null)
const showDetail = ref(false)

async function loadData(page = 1) {
  pageData.value = await request(
    `/admin/choices?keyword=${encodeURIComponent(keyword.value)}&page=${page}&page_size=8`
  )
}

async function openDetail(row) {
  selected.value = row
  detail.value = await request(`/admin/students/${row.id}/choices`)
  showDetail.value = true
}

onMounted(loadData)
</script>

<template>
  <div class="panel">
    <div class="panel-head">
      <div>
        <div class="eyebrow">Choice Review</div>
        <h3>志愿管理</h3>
      </div>
      <span class="count-pill">共 {{ pageData.total }} 名学生</span>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <input v-model="keyword" class="input" placeholder="按姓名或学号查询" />
        <button class="btn" @click="loadData()">查询</button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="table choice-table">
        <thead>
          <tr>
            <th>学号</th>
            <th>姓名</th>
            <th>成绩</th>
            <th>状态</th>
            <th>志愿数量</th>
            <th>志愿概览</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in pageData.items" :key="row.id">
            <td>{{ row.student_no }}</td>
            <td>{{ row.name }}</td>
            <td>{{ row.score }}</td>
            <td>{{ row.status }}</td>
            <td>{{ row.choice_count }}</td>
            <td class="multiline">{{ row.choices_text || '暂未填报' }}</td>
            <td><button class="btn small" @click="openDetail(row)">查看详情</button></td>
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

  <div v-if="showDetail" class="modal-mask">
    <div class="modal-card">
      <div class="modal-head">
        <div>
          <div class="eyebrow">Choice Detail</div>
          <h3>{{ selected?.name }} 的志愿</h3>
        </div>
        <button class="ghost-close" @click="showDetail = false">×</button>
      </div>
      <div class="choice-list">
        <div v-for="item in detail" :key="item.id" class="choice-item">
          <strong>第 {{ item.choice_order }} 志愿</strong>
          <span>{{ item.batch }} / {{ item.college }} / {{ item.major }}</span>
          <em>{{ item.status }}</em>
        </div>
        <div v-if="!detail.length" class="meta">该学生暂未填报志愿。</div>
      </div>
    </div>
  </div>
</template>
